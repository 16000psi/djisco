from datetime import datetime
from http import HTTPStatus

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from users.models import User


def bulk_event_creator(num, organiser, ends_at):
    for i in range(num):
        new_event = {}
        if ends_at < timezone.now():
            new_event["title"] = f"future_event_{i}"
        else:
            new_event["title"] = f"past_event_{i}"
        new_event["starts_at"] = ends_at - timezone.timedelta(hours=1)
        new_event["organiser"] = organiser
        new_event["contact"] = organiser
        new_event["ends_at"] = ends_at
        new_event["location"] = f"past_event_{i}_location"
        new_event["description"] = f"past_event_{i}_description"
        new_event["maximum_attendees"] = 15
        Event.objects.create(**new_event)


class ListTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        new_user = User.objects.create(username="b", password="b")

        # Create three past events
        bulk_event_creator(3, new_user, timezone.now() - timezone.timedelta(hours=1))

        # Create three future events
        bulk_event_creator(3, new_user, timezone.now() + timezone.timedelta(hours=1))

    def test_list_view_returns_response(self):
        url = reverse("event_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_future_events_filter(self):
        """
        View when="future" url parameter limits shown events to future

        The event_list view accepts a URL parameter, "when", which is used
        to specify whether to show future, past, or all events to the user.
        This test checks that when the value of the url parameter is
        "future", that only events with ends_at > timezone.now() are shown.
        """
        url = reverse("event_list", args=["future", 1])
        response = self.client.get(url)
        events = response.context["page_obj"].object_list

        for event in events:
            self.assertTrue(event.ends_at > timezone.now())

    def test_past_events_filter(self):
        """
        View when="past" url parameter limits shown events to past

        The event_list view accepts a URL parameter, "when", which is used
        to specify whether to show future, past, or all events to the user.
        This test checks that when the value of the url parameter is
        "past", that only events with ends_at < timezone.now() are shown.
        """
        url = reverse("event_list", args=["past", 1])
        response = self.client.get(url)
        events = response.context["page_obj"].object_list

        for event in events:
            self.assertTrue(event.ends_at < timezone.now())

    def test_all_events_filter(self):
        """
        View when="all" url parameter shows all events in results

        The event_list view accepts a URL parameter, "when", which is used
        to specify whether to show future, past, or all events to the user.
        This test checks that when the value of the url parameter is
        "all", all events are shown regardless of their ends_at value.
        """
        url = reverse("event_list", args=["all", 1])
        response = self.client.get(url)
        events = response.context["page_obj"].object_list
        events_ends_at_list = [event.ends_at for event in events]

        self.assertTrue(timezone.now() > min(events_ends_at_list))
        self.assertTrue(timezone.now() < max(events_ends_at_list))

    def test_incorrect_filter_returns_404(self):
        """
        Test that a 404 is returned if first url parameter "when" invalid
        """

        url = "events/nonsense/1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class ListQueryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create(username="b", password="b")
        cls.url = reverse("event_list", args=["future", 1])

    def test_query_counts(self):
        """
        Ensure that there is not an n+1 query on the list view

        This test asserts that the number of db queries that the list view
        incurrs with multiple events present is only one more than that it incurs
        when it is empty.
        """

        # Arrange
        def call_route():
            self.client.get(self.url)

        with CaptureQueriesContext(connection) as ctx:
            self.client.get(self.url)
            # Arrange - get the number of queries present with 0 events
            queries_without_events = len(ctx.captured_queries)
            expected_queries_with_events = queries_without_events + 1

            # Act - Create three future events
            bulk_event_creator(
                3, self.new_user, timezone.now() + timezone.timedelta(hours=1)
            )

            # Assert - Extra events have resulted in only one more query
            self.assertNumQueries(expected_queries_with_events, call_route)


class DetailTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        new_user = User.objects.create(username="b", password="b")
        cls.event = Event.objects.create(
            title="event01",
            organiser=new_user,
            contact=new_user,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )

    def test_detail_view_returns_200_response(self):
        url = reverse("event_detail", args=[self.event.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)


class LoginViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create(username="b")
        cls.new_user.set_password("b")
        cls.new_user.save()

    def test_login_success(self):
        """
        LoginView success.

        Tests that a user can login and is redirected to the event list
        view by default upon login.
        """
        login_url = reverse("login")
        response = self.client.post(
            login_url, {"username": self.new_user.username, "password": "b"}
        )

        self.assertRedirects(response, reverse("event_list"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_signed_out_user_navigation(self):
        """
        Navigation for unauthenticated user is correct.

        The header navigation should contain options to log in and sign up
        if a user is not logged in, but not an option to sign out.
        """
        response = self.client.get(reverse("event_list"))

        self.assertContains(response, "Log In")
        self.assertContains(response, "Sign Up")
        self.assertNotContains(response, "Log Out")

    def test_signed_in_user_navigation(self):
        """
        Navigation for authenticated user is correct.

        The header navigation should contain the option to sign out if a
        user is logged in, but not an option to log in or sign up.
        """
        self.client.login(username=self.new_user.username, password="b")
        response = self.client.get(reverse("event_list"))

        self.assertNotContains(response, "Log In")
        self.assertNotContains(response, "Sign Up")
        self.assertContains(response, "Log Out")
