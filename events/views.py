from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models, transaction
from django.db.models import Max, Min
from django.db.models.functions import Coalesce
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from users.models import User

from .constants import TimeFilterOptions
from .forms import ContributionForm, DeleteEventForm, EventCreateForm, EventForm
from .mixins import AuthenticatedEventOrganiserMixin
from .models import (
    RSVP,
    ContributionItem,
    ContributionRequirement,
    Event,
)


def get_all_events_maximum_attendees_aggregate():
    return Event.objects.aggregate(
        max_attendees=Coalesce(Max("maximum_attendees"), 0),
        min_attendees=Coalesce(Min("maximum_attendees"), 0),
    )


class EventListView(ListView):
    paginate_by = 5

    def get_time_filter(self) -> tuple[str, models.Q]:
        when = self.kwargs.get("when", "future")
        try:
            return TimeFilterOptions.get_option(when)
        except ValueError:
            raise Http404()

    def get_queryset(self):
        _, event_order, event_filter = self.get_time_filter()
        qs = (
            Event.objects.with_attendance_fields()
            .filter(event_filter)
            .order_by(event_order)
        )
        if self.request.user.is_authenticated:
            qs = qs.with_has_user_rsvp(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        title, _, _ = self.get_time_filter()
        when = self.kwargs.get("when", "future")

        attendees_aggregate = get_all_events_maximum_attendees_aggregate()

        return super().get_context_data(
            when=when,
            title=title,
            attendees_max=attendees_aggregate["max_attendees"],
            attendees_min=attendees_aggregate["min_attendees"],
            now=timezone.now(),
            button_text_unattend="Cancel",
            button_text_attend="Join!",
            **kwargs,
        )


class EventDetailView(DetailView):
    def get_queryset(self):
        qs = Event.objects.with_attendance_fields()
        if self.request.user.is_authenticated:
            qs = qs.with_has_user_rsvp(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(
            form=ContributionForm,
            button_text_unattend="Cancel your attendance",
            button_text_attend="Join this Event!",
            now=timezone.make_aware(datetime.now()),
            **kwargs,
        )
        event = context["event"]
        context[
            "contribution_requirements"
        ] = ContributionItem.objects.filter_for_event(event).with_counts_for_event(
            event
        )
        return context


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


class EventCreateView(LoginRequiredMixin, CreateView):
    template_name = "events/event_form.html"
    form_class = EventCreateForm

    def get_initial(self):
        initial = super().get_initial()
        initial["contact"] = self.request.user
        return initial

    def get_success_url(self):
        return reverse_lazy("event_detail", args=[self.object.id])

    def form_valid(self, form):
        event = form.save(commit=False)
        event.organiser = self.request.user
        event.save()
        RSVP.objects.create(user=self.request.user, event=event)
        messages.success(self.request, "Event created successfully!")
        return super().form_valid(form)


class EventUpdateView(AuthenticatedEventOrganiserMixin, UpdateView):
    form_class = EventForm
    model = Event

    def get_success_url(self):
        return reverse_lazy("event_detail", args=[self.object.id])

    def form_valid(self, form):
        if form.has_changed():
            messages.success(self.request, "Event modified successfully!")
        return super().form_valid(form)


class EventDeleteView(AuthenticatedEventOrganiserMixin, DeleteView):
    template_name = "events/event_delete.html"
    success_url = reverse_lazy("event_list")
    form_class = DeleteEventForm
    model = Event


def contribution_edit_view(request, pk):
    if not request.user.is_authenticated:
        error_message = "Unauthorised to modify Event attendance"
        return HttpResponseForbidden(error_message)
    if request.method == "POST":
        form = ContributionForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            redirect_target = request.POST.get("redirect_target", "/")
            contribution_title = cleaned_data.get("contribution_item")
            contribution_quantity = cleaned_data.get("quantity")

            contribution_item, _ = ContributionItem.objects.get_or_create(
                title=contribution_title
            )
            event = Event.objects.get(pk=pk)

            for i in range(contribution_quantity):
                ContributionRequirement.objects.create(
                    event=event, contribution_item=contribution_item
                )

            return HttpResponseRedirect(redirect_target)
    else:
        form = ContributionForm()
        return render(
            request,
            "events/contribution_edit.html",
            {"form": form},
        )
