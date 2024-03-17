from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from events.models import (
    RSVP,
    ContributionCommitment,
    ContributionItem,
    ContributionRequirement,
    Event,
)

from .models import Profile, User

# Create your views here.


class ProfileView(DetailView):
    model = Profile
    template_name = "users/profile_detail.html"

    def get_object(self):
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)
        return get_object_or_404(Profile, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object().user
        events = Event.objects.for_user(user)
        context["events"] = events
        return context
