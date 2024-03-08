from datetime import datetime
from http import HTTPStatus
from unittest.mock import ANY, patch

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

    def test_create_view_returns_200_response_if_authenticated(self):
        """
        If user is authenticated, view should return 200 response
        """
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_to_login_if_unauthenticated(self):
        """
        If user is not authenticated, view should redirect to login
        """
        response = self.client.post(self.url)
        expected_params = f"?next={self.url}"
        self.assertRedirects(response, reverse("login") + expected_params)

    def test_create_view_redirects_to_detail_on_success(self):
        """
        If a user is authenticated the view should redirect to the detail view

        event_create_view should redirect to the detail view of the new event
        upon correct submission.
        """
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, self.event_data)
        self.assertRedirects(response, reverse("event_detail", args=[1]))

    def test_create_view_gives_success_message(self):
        """
        Successfully creating a event should add a success message
        """
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, self.event_data)
        messages = list(django_messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Event created successfully!")
        self.assertEqual(messages[0].level, django_messages.constants.SUCCESS)

    def test_create_view_adds_event_and_RSVP(self):
        """
        If a user is authenticated the view should add a event and RSVP

        The event_create_view should allow a valid form to be submitted.
        If a valid form is submitted then the view should create a new
        event record with the form and then an RSVP, recording that the
        oragniser is attending the Event.
        """
        self.client.force_login(self.new_user)
        self.client.post(self.url, self.event_data)

        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(RSVP.objects.count(), 1)
        self.assertEqual(RSVP.objects.first().user, self.new_user)

        event = Event.objects.first()

        expected_values = {
            "title": "event01",
            "contact": self.new_user,
            "starts_at": timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            "ends_at": timezone.make_aware(datetime(2025, 10, 10, 16, 30, 0)),
            "location": "here",
            "description": "brillientay",
            "maximum_attendees": 20,
        }

        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                actual_value = getattr(event, field)
                self.assertEqual(actual_value, expected_value)

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

    def test_view_uses_form_with_is_create_true(self):
        """
        The create view should use the EventForm with is_create set to True

        EventForm uses an is_create boolean flag as part of validation. If
        set to true then the form will not validate for events in the past
        (this behaviour is what we want when creating a event, but not updating
        one).  We need is_create to be set to True for the create view so
        that the user cannot create a event in the past.
        """
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertTrue(form.is_create)

    def test_form_populated_with_correct_contact_value(self):
        """
        The contact field should be prepopulated with the current user

        For a get request the event_create_view should prepopulate the
        form's organiser field with the current logged in user.
        """
        expected_contact = self.new_user
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)
        actual_contact = response.context["form"].initial["contact"]

        self.assertEqual(expected_contact, actual_contact)


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

    def test_update_view_returns_200_response_if_authenticated_organiser(self):
        """
        If user is logged in as the organiser, view should return 200 response
        """
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_to_login_if_unauthenticated(self):
        """
        If user is not logged in then view should redirect to login
        """
        response = self.client.post(self.url)
        expected_params = f"?next={self.url}"
        self.assertRedirects(response, reverse("login") + expected_params)

    def test_redirect_to_list_view_if_not_organiser(self):
        """
        If user is logged in not as the organiser then view should redirect to list

        Event records should only be modifiable by the organiser of
        that Event (a field on the Event model, the creator of the Event).
        """
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("event_list"))

    def test_gives_warning_message_if_not_organiser(self):
        """
        If user is logged in not as organiser then message should be displayed
        """
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        messages = list(django_messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You cannot modify another user's event.")
        self.assertEqual(messages[0].level, django_messages.constants.WARNING)

    def test_update_view_redirects_to_detail_view_on_success(self):
        """
        If a user is authenticated the view should redirect to the detail view

        event_update_view should redirect to the detail view for the updated event
        upon correct submission.
        """
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, self.event_data)
        self.assertRedirects(response, reverse("event_detail", args=[1]))

    def test_update_view_edits_event(self):
        """
        The view should correctly update a Event record if the form is valid

        If the user is logged in as the organiser of the event and they submit
        a valid form via post request, the view should update the record for the
        event with the new form data.
        """
        self.client.force_login(self.new_user)
        self.client.post(self.url, self.event_data)

        self.event.refresh_from_db()
        self.assertEqual(self.event.location, self.new_location)

    def test_update_view_gives_success_message(self):
        """
        Successfully updating a event should add a success message
        """
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, self.event_data)
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

        unchanged_data = {**self.event_data, "location": "here"}
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

    def test_view_uses_form_with_is_create_false(self):
        """
        The update view should use the EventForm with is_create set to False

        EventForm uses an is_create boolean flag as part of validation. If
        set to true then the form will not validate for events in the past
        (this behaviour is what we want when creating a event, but not updating
        one).  We need is_create to be set to false for the update view during
        post requests so that that we can edit events from the past.
        """
        with patch("events.views.EventForm") as MockEventForm:
            instance = MockEventForm.return_value
            instance.is_valid.return_value = True
            instance.has_changed.return_value = True

            self.client.force_login(self.new_user)
            self.client.post(self.url, self.event_data)

            MockEventForm.assert_called_once_with(ANY, instance=ANY, is_create=False)

    def test_form_populated_with_correct_event_values(self):
        """
        The update form should be rendered with the correct event data
        """
        expected_event_data = {
            "title": "event01",
            "contact": self.new_user.id,
            "starts_at": datetime(2025, 10, 10, 14, 30, tzinfo=timezone.utc),
            "ends_at": datetime(2026, 10, 10, 15, 30, tzinfo=timezone.utc),
            "location": "here",
            "description": "brillientay",
            "maximum_attendees": 20,
        }

        self.client.force_login(self.new_user)
        response = self.client.get(self.url)
        form = response.context["form"]

        for key, expected_value in expected_event_data.items():
            with self.subTest(key=key):
                initial_value = form.initial[key]
                self.assertEqual(expected_value, initial_value)


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

    def test_delete_view_returns_200_response_if_authenticated_organiser(self):
        """
        If logged in as event organiser the view should return a 200 response
        """
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

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

    def test_delete_view_redirects_to_list_on_success(self):
        """
        If a user is authenticated the view should redirect to the list view

        event_delete_view should redirect to the list view upon
        correct submission.
        """
        self.client.force_login(self.new_user)
        response = self.client.post(self.url, {"confirm": "DELETE"})
        self.assertRedirects(response, reverse("event_list"))

    def test_delete_view_deletes_event(self):
        """
        If the form is correctly submitted then the event record should be deleted

        Users wishing to delete a event must type "DELETE" to confirm.  If this is
        done correctly when submitting, the event should be deleted.
        """

        self.client.force_login(self.new_user)
        self.client.post(self.url, {"confirm": "DELETE"})

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
