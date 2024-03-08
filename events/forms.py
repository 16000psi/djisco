from django import forms

from users.models import User


class EventForm(forms.Form):
    title = forms.CharField(max_length=200)
    contact = forms.ModelChoiceField(queryset=User.objects.all())
    maximum_attendees = forms.IntegerField()
    starts_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    ends_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    location = forms.CharField(max_length=400)
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        max_length=2000,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")

        if starts_at and ends_at:
            if ends_at < starts_at:
                self.add_error("ends_at", "Events cannot end before they have begun!")

        return cleaned_data


class DeleteEventForm(forms.Form):
    confirm = forms.CharField(max_length=6)

    def clean_confirm(self):
        confirm = self.cleaned_data.get("confirm")
        if confirm != "DELETE":
            raise forms.ValidationError(
                "That doesn't match - are you typing 'DELETE' into the confirmation box?"
            )
        return confirm
