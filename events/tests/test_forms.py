from django import forms
from django.test import TestCase
from django.utils import timezone
from events.forms import DeleteEventForm, EventCreateForm, EventForm

from users.models import User


class EventFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")

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

    def test_update_starts_at_in_past_is_valid(self):
        """
        EventForm must accept a start_date in the past
        """
        form = EventForm(
            {
                "title": "Test Event",
                "contact": self.user.id,
                "maximum_attendees": 5,
                "starts_at": timezone.now() - timezone.timedelta(days=1),
                "ends_at": timezone.now() + timezone.timedelta(hours=2),
                "location": "Test Location",
                "description": "Test Description",
            },
        )

        self.assertTrue(form.is_valid())

    def test_maximum_attendees_less_than_one_raises_error(self):
        """
        EventForm must raise an error if maximum_attendees < 1
        """
        form = EventForm(
            {
                "title": "Test Event",
                "contact": self.user.id,
                "maximum_attendees": 0,
                "starts_at": timezone.now() + timezone.timedelta(hours=1),
                "ends_at": timezone.now() + timezone.timedelta(hours=2),
                "location": "Test Location",
                "description": "Test Description",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["maximum_attendees"],
            ["You must allow for at least one attendee!"],
        )

    def test_ends_at_before_starts_at_raises_error(self):
        """
        EventForm must raise an error if ends_at is before starts_at
        """
        form = EventForm(
            {
                "title": "Test Event",
                "contact": self.user.id,
                "maximum_attendees": 5,
                "starts_at": timezone.now() + timezone.timedelta(hours=2),
                "ends_at": timezone.now() + timezone.timedelta(hours=1),
                "location": "Test Location",
                "description": "Test Description",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["ends_at"], ["Events cannot end before they have begun!"]
        )
        self.assertEqual(len(form.errors), 1)


class EventCreateFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")

    def test_starts_at_in_past_gives_error(self):
        """
        EventCreateForm must error if start_date is in the past
        """
        form = EventCreateForm(
            {
                "title": "Test Event",
                "contact": self.user.id,
                "maximum_attendees": 5,
                "starts_at": timezone.now() - timezone.timedelta(days=1),
                "ends_at": timezone.now() + timezone.timedelta(hours=2),
                "location": "Test Location",
                "description": "Test Description",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["starts_at"], ["You cannot create a event in the past!"]
        )
        self.assertEqual(len(form.errors), 1)


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
