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
            title="event01",
            organiser=new_user_01,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )
        cls.event_02 = Event.objects.create(
            title="event02",
            organiser=new_user_02,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=1,
        )
        RSVP.objects.create(event=cls.event_01, user=new_user_01)
        RSVP.objects.create(event=cls.event_01, user=new_user_02)
        RSVP.objects.create(event=cls.event_01, user=new_user_03)
        RSVP.objects.create(event=cls.event_02, user=new_user_01)
        RSVP.objects.create(event=cls.event_02, user=new_user_02)
        RSVP.objects.create(event=cls.event_02, user=new_user_03)

        cls.event_queryset = Event.objects.with_attendance_fields()
        cls.event_with_spaces = cls.event_queryset.get(pk=1)
        cls.event_oversubscribed = cls.event_queryset.get(pk=2)

    def test_event_manager_with_attendance_fields_attendee_count(self):
        """
        The Event with_attendance_fields manager method should add an
        attendee_count property to each instance in the queryset, which is the
        total number of attendees to the event. (RSVP records relating to the
        event).
        """
        expected_attendee_count = 3
        actual_attendee_count = self.event_with_spaces.attendee_count
        self.assertEqual(expected_attendee_count, actual_attendee_count)

    def test_with_attendance_fields_remaining_spaces_correct_if_positive(self):
        """
        The Event with_attendance_fields manager method should add a
        remaining_spaces property to each instance in the queryset, which is
        the total number or ramining spaces left for the event
        (maximum_attendees - attendee_count). It should be accurate when
        there are spaces left.
        """
        expected_remaining_spaces = 17
        actual_remaining_spaces = self.event_with_spaces.remaining_spaces
        self.assertEqual(expected_remaining_spaces, actual_remaining_spaces)

    def test_with_attendance_fields_remaining_spaces_not_less_than_zero(self):
        """
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

