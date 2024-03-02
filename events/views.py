from django.shortcuts import render, get_object_or_404

from .models import Event


def event_list(request):
    events = Event.objects.all().order_by("starts_at")
    context = {
        "events": events,
    }
    return render(request, "events/event_list.html", context)


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    context = {
        "event": event,
    }
    return render(request, "events/event_detail.html", context)
