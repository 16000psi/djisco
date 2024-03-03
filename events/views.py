from datetime import datetime

from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import Event


def event_list(request, when="future"):
    if when == "all":
        events = Event.objects.all().order_by("-starts_at")
        title = "All Events"
    elif when == "future":
        events = Event.objects.in_future().order_by("-starts_at")
        title = "Events"
    elif when == "past":
        events = Event.objects.in_past().order_by("-starts_at")
        title = "Past Events"
    else:
        raise Http404("Page not found")

    pagination_limit = 5
    paginator = Paginator(events, pagination_limit)

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
    return render(request, "events/event_list.html", context)


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    context = {
        "event": event,
        "now": timezone.make_aware(datetime.now()),
    }
    return render(request, "events/event_detail.html", context)
