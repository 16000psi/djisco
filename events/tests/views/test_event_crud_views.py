from datetime import datetime
from http import HTTPStatus

from django.contrib import messages as django_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import RSVP, Event
from users.models import User


class EventCreateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create_user(username="b", password="b")
        cls.event_data = {
            "title": "event01",
            "contact": cls.new_user.id,
            "starts_at": "2025-10-10T14:30:00",
            "ends_at": "2025-10-10T16:30:00",
            "location": "here",
            "description": "brillientay",
            "maximum_attendees": 20,
        }
        cls.url = reverse("event_new")

    def test_redirect_to_login_if_unauthenticated(self):
        """
        If user is not authenticated, view should redirect to login
        """
        response = self.client.post(self.url)
        expected_params = f"?next={self.url}"
        self.assertRedirects(response, reverse("login") + expected_params)

    def test_get_request_happy_path(self):
        # Arrange
        self.client.force_login(self.new_user)

        # Act
        response = self.client.get(self.url)

        # Assert - correct response code
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert - Correct template used
        self.assertTemplateUsed(response, "events/event_form.html")

        # Assert - Form is in context
        self.assertIn("form", response.context)

        # Assert - Correct title and submit_text in context
        self.assertEqual(response.context["title"], "Create Event")
        self.assertEqual(response.context["submit_text"], "Create new event")

        # Assert - Form contact prepopulated with current user
        expected_contact = self.new_user
        actual_contact = response.context["form"].initial["contact"]
        self.assertEqual(expected_contact, actual_contact)

    def test_post_request_happy_path(self):
        # Arrange
        expected_values = {
            "title": "event01",
            "organiser": self.new_user,  # Organiser must be submitter
            "contact": self.new_user,
            "starts_at": timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            "ends_at": timezone.make_aware(datetime(2025, 10, 10, 16, 30, 0)),
            "location": "here",
            "description": "brillientay",
            "maximum_attendees": 20,
        }
        self.client.force_login(self.new_user)

        # Act
        response = self.client.post(self.url, self.event_data)

        event = Event.objects.first()

        # Assert - Event created with correct data
        self.assertEqual(Event.objects.count(), 1)
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                actual_value = getattr(event, field)
                self.assertEqual(actual_value, expected_value)

        # Assert - RSVP created for organiser and new event
        rsvps = RSVP.objects.filter(event=event)
        self.assertEqual(rsvps.count(), 1)
        self.assertEqual(rsvps.first().user, self.new_user)
        self.assertEqual(rsvps.first().event, event)

        # Assert - Redirects to detail view for new event
        self.assertRedirects(response, reverse("event_detail", args=[1]))

        # Assert - Gives success message
        messages = list(django_messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Event created successfully!")
        self.assertEqual(messages[0].level, django_messages.constants.SUCCESS)

    def test_starts_at_lt_now_invalid(self):
        """
        Is is not possible to create a event that is in the past

        If the user attempts to create a event where the value of
        starts_at is less than the current datetime, there should be
        no change to the database and the view should not redirect.
        """

        new_event_in_past = {
            **self.event_data,
            "starts_at": timezone.now() - timezone.timedelta(days=1),
            "ends_at": timezone.now() - timezone.timedelta(days=0.5),
        }

        self.client.force_login(self.new_user)
        response = self.client.post(self.url, new_event_in_past)

        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(RSVP.objects.count(), 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_ends_at_lt_starts_at_invalid(self):
        """
        Is is not possible to create a event where ends_at is < starts_at

        If the user attempts to create a event where the value of
        starts_at is less than starts_at, there should be
        no change to the database and the view should not redirect.

        """

        new_event_ends_before_starts = {
            **self.event_data,
            "starts_at": timezone.now() + timezone.timedelta(hours=2),
            "ends_at": timezone.now() + timezone.timedelta(hours=1),
        }

        self.client.force_login(self.new_user)
        response = self.client.post(self.url, new_event_ends_before_starts)

        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(RSVP.objects.count(), 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_max_attendees_lt_one_is_invalid(self):
        """
        Is is not possible to create a event with < 1 maximum_attendees

        If the user attempts to create a event where the value of
        maximum_attendees is less than one, there should be
        no change to the database and the view should not redirect.
        """

        new_event_zero_max_attendees = {
            **self.event_data,
            "maximum_attendees": 0,
        }

        self.client.force_login(self.new_user)
        response = self.client.post(self.url, new_event_zero_max_attendees)

        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(RSVP.objects.count(), 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class EventUpdateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create_user(username="b", password="b")
        cls.other_user = User.objects.create_user(username="c", password="c")

        cls.event = Event.objects.create(
            title="event01",
            organiser=cls.new_user,
            contact=cls.new_user,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )
        cls.new_location = "there"
        cls.event_data = {
            "title": "event01",
            "contact": cls.new_user.id,
            "starts_at": "2025-10-10T14:30:00",
            "ends_at": "2026-10-10T15:30:00",
            "location": cls.new_location,
            "description": "brillientay",
            "maximum_attendees": 20,
        }
        cls.url = reverse("event_edit", args=[cls.event.pk])

    def test_redirect_to_login_if_unauthenticated(self):
        response = self.client.post(self.url)
        expected_params = f"?next={self.url}"
        self.assertRedirects(response, reverse("login") + expected_params)

    def test_not_event_organiser(self):
        # Arrange - log in as non-organiser user
        self.client.force_login(self.other_user)

        # Act
        response = self.client.post(self.url)

        # Assert - redirects to event list
        self.assertRedirects(response, reverse("event_list"))

        # Assert - gives warning message
        messages = list(django_messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You cannot modify another user's event.")
        self.assertEqual(messages[0].level, django_messages.constants.WARNING)

    def test_get_request_happy_path(self):
        # Arrange
        self.client.force_login(self.new_user)

        # Act
        response = self.client.get(self.url)

        # Assert - correct response code
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert - Correct template used
        self.assertTemplateUsed(response, "events/event_form.html")

        # Assert - Correct title and submit_text in context
        self.assertEqual(response.context["title"], "Update Event")
        self.assertEqual(response.context["submit_text"], "Save changes to event")

        # Assert - Form is in context with correct initial data
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertEqual(form.initial["title"], self.event.title)
        self.assertEqual(form.initial["contact"], self.event.contact.id)
        self.assertEqual(
            form.initial["maximum_attendees"], self.event.maximum_attendees
        )
        self.assertEqual(form.initial["starts_at"], self.event.starts_at)
        self.assertEqual(form.initial["ends_at"], self.event.ends_at)
        self.assertEqual(form.initial["location"], self.event.location)
        self.assertEqual(form.initial["description"], self.event.description)

    def test_post_request_happy_path(self):
        # Arrange
        new_location = "there"
        event_data = {
            "title": self.event.title,
            "contact": self.new_user.id,
            "starts_at": self.event.starts_at,
            "ends_at": self.event.ends_at,
            "location": new_location,
            "description": self.event.description,
            "maximum_attendees": self.event.maximum_attendees,
        }
        expected_event_count = Event.objects.count()

        # Act
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, event_data)

        # Assert - redirects to detail view for updated event
        self.assertRedirects(response, reverse("event_detail", args=[1]))

        # Assert - correctly modifies event record in database
        self.event.refresh_from_db()
        self.assertEqual(self.event.location, self.new_location)
        actual_event_count = Event.objects.count()
        self.assertEqual(expected_event_count, actual_event_count)

        # Assert - gives success message
        messages = list(django_messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Event modified successfully!")
        self.assertEqual(messages[0].level, django_messages.constants.SUCCESS)

    def test_update_view_no_message_if_no_change(self):
        """
        If a event is updated without any changes don't display a message

        The view should detect whether or not the data has actually
        changed from its initial state, and a message should only be shown
        in the case that it has changed.
        """

        unchanged_data = {
            "title": self.event.title,
            "contact": self.new_user.id,
            "starts_at": self.event.starts_at,
            "ends_at": self.event.ends_at,
            "location": self.event.location,
            "description": self.event.description,
            "maximum_attendees": self.event.maximum_attendees,
        }
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, unchanged_data)
        messages = list(django_messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 0)

    def test_ends_at_lt_now_valid(self):
        """
        Submitting an update view form with a starts_at lt < now is valid

        Unlike the event_create_view, submitting to the event_update_view
        a event with a starts_at date in the past should result in the
        event record in question being updated, as we want the user to be
        able to edit events from the past.
        """

        edited_past_event_attributes = {
            **self.event_data,
            "starts_at": timezone.now() - timezone.timedelta(hours=2),
            "ends_at": timezone.now() - timezone.timedelta(hours=1),
        }

        self.client.force_login(self.new_user)
        self.client.post(self.url, edited_past_event_attributes)

        possibly_updated_event = Event.objects.first()

        for field_name, expected_val in edited_past_event_attributes.items():
            with self.subTest(field_name=field_name):
                if field_name != "contact":
                    self.assertEqual(
                        getattr(possibly_updated_event, field_name),
                        expected_val,
                    )
                else:
                    self.assertEqual(
                        getattr(possibly_updated_event, "contact").pk,
                        expected_val,
                    )

    def test_ends_at_lt_starts_at_invalid(self):
        """
        Is is not possible to update a event where ends_at is < starts_at

        If the user attempts to update a event where the value of
        starts_at is less than starts_at, there should be
        no change to the event record and the view should not redirect.

        """

        new_event_ends_before_starts = {
            **self.event_data,
            "starts_at": timezone.now() + timezone.timedelta(hours=2),
            "ends_at": timezone.now() + timezone.timedelta(hours=1),
        }

        self.client.force_login(self.new_user)
        response = self.client.post(self.url, new_event_ends_before_starts)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        possibly_updated_event = Event.objects.first()

        for field in self.event._meta.fields:
            field_name = field.name
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    getattr(possibly_updated_event, field_name),
                    getattr(self.event, field_name),
                )

    def test_max_attendees_lt_one_is_invalid(self):
        """
        Is is not possible to update a event with < 1 maximum_attendees

        If the user attempts to update a event where the value of
        maximum_attendees is less than one, there should be
        no change to the event record and the view should not redirect.
        """

        new_event_zero_max_attendees = {
            **self.event_data,
            "maximum_attendees": 0,
        }

        self.client.force_login(self.new_user)
        response = self.client.post(self.url, new_event_zero_max_attendees)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        possibly_updated_event = Event.objects.first()

        for field in self.event._meta.fields:
            field_name = field.name
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    getattr(possibly_updated_event, field_name),
                    getattr(self.event, field_name),
                )

    def test_update_view_cannot_change_organiser(self):
        """
        The user cannot submit to this view and change the Event organiser

        The event organiser is automatically by the event_create_view to
        be the user who created the event. This test checks that the update
        view cannot be used to change this later.
        """
        altered_organiser_data = {**self.event_data, "organiser": self.other_user}
        self.client.force_login(self.new_user)
        self.client.post(self.url, altered_organiser_data)
        self.event.refresh_from_db()

        self.assertEqual(self.event.organiser, self.new_user)


class EventDeleteViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create_user(username="b", password="b")
        cls.other_user = User.objects.create_user(username="c", password="c")

        cls.event = Event.objects.create(
            title="event01",
            organiser=cls.new_user,
            contact=cls.new_user,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )
        cls.url = reverse("event_delete", args=[cls.event.pk])

    def test_redirect_to_login_if_unauthenticated(self):
        """
        If not logged in then the view should redirect the user to login
        """
        response = self.client.post(self.url)
        expected_params = f"?next={self.url}"
        self.assertRedirects(response, reverse("login") + expected_params)

    def test_redirect_to_list_view_if_not_organiser(self):
        """
        If logged in not as organiser then view should redirect to the list view
        """
        self.client.login(username="c", password="c")
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("event_list"))

    def test_get_request_happy_path(self):
        # Arrange
        self.client.force_login(self.new_user)

        # Act
        response = self.client.get(self.url)

        # Assert - correct status code
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert - Correct template used
        self.assertTemplateUsed(response, "events/event_delete.html")

        # Assert - Form and event are in context
        self.assertIn("form", response.context)
        self.assertIn("event", response.context)

        # Assert - Correct event in context
        self.assertEqual(response.context["event"], self.event)

    def test_post_request_happy_path(self):
        # Arrange
        self.client.force_login(self.new_user)

        # Act
        response = self.client.post(self.url, {"confirm": "DELETE"})

        # Assert - redirects to list view on success
        self.assertRedirects(response, reverse("event_list"))

        # Assert - deletes event record
        self.assertEqual(Event.objects.count(), 0)

    def test_delete_view_form_invalid(self):
        """
        With form is incorrectly submitted the event record should be preserved

        Users wishing to delete a event must type "DELETE" to confirm.  If this is
        done incorrectly when submitting, the event should not be deleted.
        """
        self.client.force_login(self.new_user)
        self.client.post(self.url, {"confirm": "wrong"})
        self.assertEqual(Event.objects.count(), 1)
