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
        events = Event.objects.for_user(user).in_future()
        past_events = Event.objects.for_user(user).in_past()
        for event in events:
            rsvp = RSVP.objects.get(user=user, event=event)
            items_pks = ContributionItem.objects.filter_for_event(event).values_list(
                "pk", flat=True
            )
            requirements_pks = ContributionRequirement.objects.filter(
                event=event, contribution_item__in=items_pks
            ).values_list("pk", flat=True)

            commitments = ContributionCommitment.objects.select_related(
                "contribution_requirement__contribution_item"
            ).filter(RSVP=rsvp, contribution_requirement__in=requirements_pks)
            commitment_dict = {}
            for commitment in commitments:
                contribution_item_title = (
                    commitment.contribution_requirement.contribution_item.title
                )
                commitment_dict[contribution_item_title] = (
                    commitment_dict.get(contribution_item_title, 0) + 1
                )
            event.commitments_for_user_by_item = [
                (key, value) for key, value in commitment_dict.items()
            ]

        context["events"] = events
        context["past_events"] = past_events
        return context
