from datetime import datetime

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

    context = {
        "events": events,
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
