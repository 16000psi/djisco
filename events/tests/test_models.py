from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from events.models import Event, RSVP
from users.models import User


class EventTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        new_user_01 = User.objects.create(username="b", password="b")
        new_user_02 = User.objects.create(username="c", password="c")
        new_user_03 = User.objects.create(username="d", password="d")
        cls.event_01 = Event.objects.create(
            title="future with space",
            organiser=new_user_01,
            starts_at=timezone.make_aware(datetime(2035, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2036, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )
        cls.event_02 = Event.objects.create(
            title="future without space",
            organiser=new_user_02,
            starts_at=timezone.make_aware(datetime(2035, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2036, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=1,
        )
        cls.event_03 = Event.objects.create(
            title="past with space",
            organiser=new_user_02,
            starts_at=timezone.make_aware(datetime(1025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(1026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=10,
        )
        RSVP.objects.create(event=cls.event_01, user=new_user_02)
        RSVP.objects.create(event=cls.event_01, user=new_user_03)
        RSVP.objects.create(event=cls.event_02, user=new_user_01)
        RSVP.objects.create(event=cls.event_02, user=new_user_02)
        RSVP.objects.create(event=cls.event_02, user=new_user_03)
        RSVP.objects.create(event=cls.event_03, user=new_user_01)
        RSVP.objects.create(event=cls.event_03, user=new_user_02)
        RSVP.objects.create(event=cls.event_03, user=new_user_03)

        cls.event_queryset = Event.objects.with_attendance_fields()
        cls.event_with_spaces = cls.event_queryset.get(pk=1)
        cls.event_oversubscribed = cls.event_queryset.get(pk=2)
        cls.event_past = cls.event_queryset.get(pk=3)

        cls.event_authenticated_queryset = Event.objects.with_has_user_rsvp(
            new_user_01
        )
        cls.event_user_attending = cls.event_authenticated_queryset.get(pk=2)
        cls.event_user_not_attending = cls.event_authenticated_queryset.get(pk=1)

    def test_event_manager_with_attendance_fields_attendee_count(self):
        """
        with_attendance_fields adds attendee_count property to events.

        The Event with_attendance_fields manager method should add an
        attendee_count property to each instance in the queryset, which is the
        total number of attendees to the event. (RSVP records relating to the
        event).
        """
        expected_attendee_count = 2
        actual_attendee_count = self.event_with_spaces.attendee_count
        self.assertEqual(expected_attendee_count, actual_attendee_count)

    def test_with_attendance_fields_remaining_spaces_correct_if_positive(self):
        """
        with_attendance_fields adds correct remaining_spaces

        The Event with_attendance_fields manager method should add a
        remaining_spaces property to each instance in the queryset, which is
        the total number or ramining spaces left for the event
        (maximum_attendees - attendee_count). It should be accurate when
        there are spaces left.
        """
        expected_remaining_spaces = 18
        actual_remaining_spaces = self.event_with_spaces.remaining_spaces
        self.assertEqual(expected_remaining_spaces, actual_remaining_spaces)

    def test_with_attendance_fields_remaining_spaces_not_less_than_zero(self):
        """
        with_attendance_fields adds correct remaining_spaces if event full

        The Event with_attendance_fields manager method should add a
        remaining_spaces property to each instance in the queryset, which is
        the total number or ramining spaces left for the event
        (maximum_attendees - attendee_count).  It should never be less than
        zero even if there are more attendees than the maximum_attendees
        value.
        """
        expected_remaining_spaces = 0
        actual_remaining_spaces = self.event_oversubscribed.remaining_spaces
        self.assertEqual(expected_remaining_spaces, actual_remaining_spaces)

    def test_event_accepting_attendees_if_conditions_met(self):
        """
        Event accepting_attendees property should be correctly set.

        Event instances each have an accepting_attendees property, which
        is a boolean that is True if the Event ends_at is in the future,
        and the attendee count is not equal to or greater than the
        maximum_attendees field. This asserts that the property is correctly
        set to True if both conditions are met.
        """
        self.assertTrue(self.event_with_spaces.accepting_attendees)

    def test_event_accepting_attendees_false_if_in_past(self):
        """
        Event accepting_attendees property should be correctly set.

        Event instances each have an accepting_attendees property, which
        is a boolean that is True if the Event ends_at is in the future,
        and the attendee count is not equal to or greater than the
        maximum_attendees field. This asserts that the property is False
        for Events whose ends_at field is less than now.
        """
        self.assertFalse(self.event_past.accepting_attendees)

    def test_event_accepting_attendees_false_if_full(self):
        """
        Event accepting_attendees property should be correctly set.

        Event instances each have an accepting_attendees property, which
        is a boolean that is True if the Event ends_at is in the future,
        and the attendee count is not equal to or greater than the
        maximum_attendees field. This asserts that the property is False
        for Events whose attendee count is equal to or greater than the
        maximum_attendees field.
        """
        self.assertFalse(self.event_oversubscribed.accepting_attendees)

    def test_with_has_user_rsvp_true_if_user_attending(self):
        """
        with_has_user_rsvp is correctly set.

        The event with_has_user_rsvp manager method should add a
        has_user_rsvp record to each instance in the queryset when
        called with a User object which is a boolean representing whether
        there is an RSVP record matching both the User and Event (whether
        the User is attending the Event). This test asserts that the field
        will be true if the user is attending.
        """
        self.assertTrue(self.event_user_attending.has_user_rsvp)

    def test_with_has_user_rsvp_false_if_user_not_attending(self):
        """
        with_has_user_rsvp is correctly set.

        The event with_has_user_rsvp manager method should add a
        has_user_rsvp record to each instance in the queryset when
        called with a User object which is a boolean representing whether
        there is an RSVP record matching both the User and Event (whether
        the User is attending the Event). This test asserts that the field
        will be false if the user is not attending.
        """
        self.assertFalse(self.event_user_not_attending.has_user_rsvp)
