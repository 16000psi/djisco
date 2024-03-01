from django.shortcuts import get_object_or_404, render

from .models import Event


def event_list(request):
    return render(request, "events/event_list.html")


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    context = {
        "event": event,
    }
    return render(request, "events/event_detail.html", context)
