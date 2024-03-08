from django import forms
from django.test import TestCase

from events.forms import DeleteEventForm, EventForm


class EventFormTest(TestCase):
    def test_event_form_has_correct_fields(self):
        """
        EventForm must contain Event model fields minus organiser

        This test checks that the correct fields are present in the EventForm.
        The fields should be the same as the Event model, minus the organiser
        which is set automatically in the view to be the logged-in user.
        """
        form = EventForm()
        expected_fields = [
            "title",
            "contact",
            "maximum_attendees",
            "starts_at",
            "ends_at",
            "location",
            "description",
        ]
        actual_fields = list(form.fields)
        self.assertCountEqual(actual_fields, expected_fields)

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertTrue(field in actual_fields)


class DeleteFormTestCase(TestCase):
    def test_event_delete_form_has_correct_fields(self):
        """
        The form should have a confirmation sequence for the user to type out
        """
        form = DeleteEventForm()
        self.assertIn("confirm", form.fields)
        self.assertIsInstance(form.fields["confirm"], forms.CharField)

    def test_form_raises_validation_error_for_confirmation_sequence(self):
        """
        Validation error raised if user inputs incorrect confirmation sequence
        """
        form = DeleteEventForm({"confirm": "wrong"})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["confirm"],
            ["That doesn't match - are you typing 'DELETE' into the confirmation box?"],
        )

    def test_form_valid_with_correct_confirmation_sequence(self):
        """
        If confirmation sequence is correct the form is valid
        """
        form = DeleteEventForm({"confirm": "DELETE"})
        self.assertTrue(form.is_valid())
