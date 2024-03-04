from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Max, Min
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import Event


def get_all_events_maximum_attendees_aggregate():
    return Event.objects.aggregate(
        max_attendees=Coalesce(Max("maximum_attendees"), 0),
        min_attendees=Coalesce(Min("maximum_attendees"), 0),
    )


def event_list(request, when="future"):
    if when == "all":
        events = Event.objects.with_attendance_fields()
        title = "All Events"
    elif when == "future":
        events = Event.objects.with_attendance_fields().in_future()
        title = "Events"
    elif when == "past":
        events = Event.objects.with_attendance_fields().in_past()
        title = "Past Events"
    else:
        raise Http404("Page not found")

    pagination_limit = 5
    paginator = Paginator(events.order_by("-starts_at"), pagination_limit)

    try:
        page_number = int(request.GET.get("page", 1))

    except ValueError:
        page_number = 1

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
    event = get_object_or_404(Event.objects.with_attendance_fields(), pk=pk)
    context = {
        "event": event,
        "now": timezone.make_aware(datetime.now()),
    }
    return render(request, "events/event_detail.html", context)
