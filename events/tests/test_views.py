from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from users.models import User


class ListTestCase(TestCase):
    def test_list_view_returns_response(self):
        url = reverse("event_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class DetailTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        new_user = User.objects.create(username="b", password="b")
        cls.event = Event.objects.create(
            title="event01",
            organiser=new_user,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
        )

    def test_detail_view_returns_200_response(self):
        url = reverse("event_detail", args=[self.event.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class LoginViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create(username="b")
        cls.new_user.set_password("b")
        cls.new_user.save()

    def test_login_success(self):
        """
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
        The header navigation should contain options to log in and sign up
        if a user is not logged in, but not an option to sign out.
        """
        response = self.client.get(reverse("event_list"))

        self.assertContains(response, "Log In")
        self.assertContains(response, "Sign Up")
        self.assertNotContains(response, "Log Out")

    def test_signed_in_user_navigation(self):
        """
        The header navigation should contain the option to sign out if a
        user is logged in, but not an option to log in or sign up.
        """
        self.client.login(username=self.new_user.username, password="b")
        response = self.client.get(reverse("event_list"))

        self.assertNotContains(response, "Log In")
        self.assertNotContains(response, "Sign Up")
        self.assertContains(response, "Log Out")
