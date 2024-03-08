from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Count, Max, Min, Q
from django.db.models.functions import Coalesce
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from users.models import User

from .forms import DeleteEventForm, EventForm
from .models import RSVP, ContributionItem, ContributionRequirement, Event


def get_events(request, when="all"):
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        if when == "all":
            events = Event.objects.with_attendance_fields().with_has_user_rsvp(user)
        elif when == "future":
            events = (
                Event.objects.with_attendance_fields()
                .with_has_user_rsvp(user)
                .in_future()
            )
        elif when == "past":
            events = (
                Event.objects.with_attendance_fields()
                .with_has_user_rsvp(user)
                .in_past()
            )

    else:
        if when == "all":
            events = Event.objects.with_attendance_fields()
        elif when == "future":
            events = Event.objects.with_attendance_fields().in_future()
        elif when == "past":
            events = Event.objects.with_attendance_fields().in_past()

    return events


def get_all_events_maximum_attendees_aggregate():
    return Event.objects.aggregate(
        max_attendees=Coalesce(Max("maximum_attendees"), 0),
        min_attendees=Coalesce(Min("maximum_attendees"), 0),
    )


def event_list(request, when="future", page=1):
    if when == "all":
        title = "All Events"
    elif when == "future":
        title = "Events"
    elif when == "past":
        title = "Past Events"
    else:
        raise Http404("Page not found")

    events = get_events(request, when)
    pagination_limit = 5
    paginator = Paginator(events.order_by("-starts_at"), pagination_limit)
    page_number = int(page)
    page_obj = paginator.get_page(page_number)
    start_index = page_obj.start_index()
    end_index = page_obj.end_index()

    pagination_message = (
        f"Displaying {start_index} - {end_index} of {len(events)} results."
    )

    context = {
        "pagination_limit": pagination_limit,
        "page_obj": page_obj,
        "pagination_message": pagination_message,
        "result_count": len(events),
        "now": timezone.make_aware(datetime.now()),
        "when": when,
        "title": title,
    }

    attendees_aggregate = get_all_events_maximum_attendees_aggregate()
    context["attendees_max"] = attendees_aggregate["max_attendees"]
    context["attendees_min"] = attendees_aggregate["min_attendees"]

    return render(request, "events/event_list.html", context)


def event_detail(request, pk):
    event = get_object_or_404(get_events(request), pk=pk)
    subquery = ContributionRequirement.objects.filter(event=event).values(
        "contribution_item_id"
    )
    contribution_requirements = ContributionItem.objects.filter(
        id__in=models.Subquery(subquery)
    ).annotate(
        requirements_count=Count(
            "contributionrequirement", filter=Q(contributionrequirement__event=event)
        ),
        commitments_count=Count(
            "contributionrequirement__contributioncommitment",
            filter=Q(contributionrequirement__event=event),
        ),
    )

    context = {
        "contribution_requirements": contribution_requirements,
        "event": event,
        "now": timezone.make_aware(datetime.now()),
    }
    return render(request, "events/event_detail.html", context)


def manage_event_attendance(request, pk, action):
    if request.user.is_authenticated:
        if request.method == "POST":
            with transaction.atomic():
                user = get_object_or_404(User, id=request.user.id)

                try:
                    event = Event.objects.select_for_update().get(pk=pk)
                except Event.DoesNotExist:
                    raise Http404(
                        "Event not found - this may have been deleted elsewhere"
                    )

                if action == "attend":
                    if event.accepting_attendees:
                        _, rsvp_created = RSVP.objects.get_or_create(
                            event=event, user=user
                        )
                        if rsvp_created:
                            data = {
                                "success": True,
                            }
                            status = 200
                        else:
                            data = {
                                "success": False,
                                "error_message": "You are already attending this Event - this may have been updated elsewhere",
                            }
                            status = 409
                    else:
                        data = {
                            "success": False,
                            "error_message": "This Event is no longer accepting attendees - it could be full, or have ended.",
                        }
                        status = 409
                elif action == "unattend":
                    try:
                        rsvp = RSVP.objects.get(event=event, user=user)
                        rsvp.delete()
                        data = {
                            "success": True,
                        }
                        status = 200
                    except RSVP.DoesNotExist:
                        data = {
                            "success": False,
                            "error_message": "You are not attending this event - this may have been updated elsewhere.",
                        }
                        status = 409

            if request.accepts("text/html"):
                redirect_target = request.POST.get("redirect_target", "/")
                return HttpResponseRedirect(redirect_target)
            elif request.accepts("application/json"):
                return JsonResponse(data, status=status)

        else:
            error_message = "Invalid request method"
            if request.accepts("text/html"):
                return HttpResponseBadRequest(error_message)
            elif request.accepts("application/json"):
                data = {
                    "success": False,
                    "error_message": error_message,
                }
                return JsonResponse(data, status=400)
    else:
        error_message = "Unauthorised to modify Event attendance"
        if request.accepts("text/html"):
            return HttpResponseForbidden(error_message)
        elif request.accepts("application/json"):
            data = {
                "success": False,
                "error_message": error_message,
            }
            return JsonResponse(data, status=403)


@login_required
def event_create_view(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organiser = request.user
            event.save()
            RSVP.objects.create(user=request.user, event=event)
            messages.success(request, "Event created successfully!")
            return redirect("event_detail", pk=event.id)
    else:
        form = EventForm(initial={"contact": request.user})
    return render(
        request,
        "events/event_form.html",
        {"form": form, "title": "Create Event", "submit_text": "Create new event"},
    )


@login_required
def event_update_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organiser != request.user:
        messages.warning(request, "You cannot modify another user's event.")
        return HttpResponseRedirect(reverse("event_list"))

    if request.method == "POST":
        form = EventForm(request.POST, instance=event, is_create=False)
        if form.is_valid():
            if form.has_changed():
                form.save()
                messages.success(request, "Event modified successfully!")
            return redirect("event_detail", pk=event.id)
    else:
        form = EventForm(instance=event)

    return render(
        request,
        "events/event_form.html",
        {
            "form": form,
            "event": event,
            "title": "Update Event",
            "submit_text": "Save changes to event",
        },
    )


@login_required
def event_delete_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.organiser != request.user:
        messages.warning(request, "You cannot modify another user's event.")
        return HttpResponseRedirect(reverse("event_list"))
    if request.method == "POST":
        form = DeleteEventForm(request.POST)
        if form.is_valid() and form.cleaned_data["confirm"] == "DELETE":
            event.delete()
            messages.info(request, "Event deleted successfully.")
            return redirect("event_list")
    else:
        form = DeleteEventForm()
    return render(request, "events/event_delete.html", {"form": form, "event": event})
