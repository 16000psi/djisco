from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Max, Min
from django.db.models.functions import Coalesce
from django.http import (
    Http404,
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponseBadRequest,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from users.models import User

from .models import RSVP, Event


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
    context = {
        "event": event,
        "now": timezone.make_aware(datetime.now()),
    }
    return render(request, "events/event_detail.html", context)


def manage_event_attendance(request, pk, action):
    if request.user.is_authenticated:
        if request.method == "POST":
            redirect_target = request.POST.get("redirect_target", "/")
            user_id = request.user.id
            event = get_object_or_404(Event, id=pk)
            user = get_object_or_404(User, id=user_id)

            if action == "attend":
                RSVP.objects.get_or_create(event=event, user=user)

            elif action == "unattend":
                try:
                    rsvp = RSVP.objects.get(event=event, user=user)
                    rsvp.delete()
                except RSVP.DoesNotExist:
                    pass
            return HttpResponseRedirect(redirect_target)
        else:
            return HttpResponseBadRequest("Invalid request method")
    else:
        return HttpResponseForbidden("Unauthorised to modify Event attendance")
