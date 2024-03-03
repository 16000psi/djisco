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
