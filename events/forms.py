from django import forms
from django.utils import timezone

from events.models import (
    ContributionRequirement,
    Event,
)


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "contact",
            "maximum_attendees",
            "starts_at",
            "ends_at",
            "location",
            "description",
        ]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "location": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_maximum_attendees(self):
        maximum_attendees = self.cleaned_data.get("maximum_attendees")
        if maximum_attendees < 1:
            raise forms.ValidationError(
                "You must allow for at least one attendee!",
                code="max_attendees_lt_one",
            )
        return maximum_attendees

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")

        if starts_at and ends_at:
            if ends_at < starts_at:
                self.add_error(
                    "ends_at",
                    forms.ValidationError(
                        "Events cannot end before they have begun!",
                        code="ends_before_starts",
                    ),
                )

        return cleaned_data


class EventCreateForm(EventForm):
    def clean_starts_at(self):
        starts_at = self.cleaned_data["starts_at"]
        if starts_at < timezone.now():
            raise forms.ValidationError(
                "You cannot create a event in the past!", code="in_past"
            )
        return starts_at


class DeleteEventForm(forms.Form):
    confirm = forms.CharField(max_length=6)

    def clean_confirm(self):
        confirm = self.cleaned_data.get("confirm")
        if confirm != "DELETE":
            raise forms.ValidationError(
                "That doesn't match - are you typing 'DELETE' into the confirmation box?"
            )
        return confirm


class ContributionForm(forms.Form):
    contribution_item = forms.CharField(label="Contribution Name")
    quantity = forms.IntegerField(min_value=1, label="Quantity")


class ContributionEditForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity")

    def __init__(self, *args, **kwargs):
        contribution_item = kwargs.pop("contribution_item", None)
        super().__init__(*args, **kwargs)
        if contribution_item is not None:
            self.fields["quantity"].initial = contribution_item.commitments_count
            self.fields["quantity"].widget.attrs[
                "min"
            ] = contribution_item.commitments_count


class CommitmentForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity")

    def __init__(self, *args, **kwargs):
        event = kwargs.pop("event")
        contribution_item = kwargs.pop("contribution_item")
        super().__init__(*args, **kwargs)
        unfulfilled_requirements = ContributionRequirement.objects.get_unfulfilled_requirements_for_item_for_event(
            contribution_item, event
        )
        if unfulfilled_requirements is not None:
            self.fields["quantity"].widget.attrs[
                "max"
            ] = unfulfilled_requirements.count()
