from datetime import datetime
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import RSVP, Event
from users.models import User


class ManageEventAttendanceTestCase(TestCase):
    @classmethod
    def setUp(self):
        self.user_01 = User.objects.create(username="b")
        self.user_01.set_password("b")
        self.user_01.save()

        self.user_02 = User.objects.create(username="c")
        self.user_02.set_password("c")
        self.user_02.save()

        self.event_01 = Event.objects.create(
            title="event01",
            organiser=self.user_01,
            contact=self.user_01,
            starts_at=timezone.make_aware(datetime(2025, 10, 10, 14, 30, 0)),
            ends_at=timezone.make_aware(datetime(2026, 10, 10, 15, 30, 0)),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )

        RSVP.objects.create(user=self.user_02, event=self.event_01)

    def test_forbidden_raised_if_not_authenticated(self):
        """
        Unauthenticated manage_event_attendance access raises HttpResponseForbidden.

        The event_attend view should only operate on the database and
        redirect in the case that the user is authenticated. Otherwise,
        it should raise a ResponseForbidden error, which has a 403 code.
        """
        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "attend"])
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_bad_request_raised_if_get_method(self):
        """
        Using GET method raises HttpResponseBadRequest.

        The event_attend view should only allow POST requests. Using GET
        should raise a ResponseBadRequest error, which has a 400 code, even
        if a user is authenticated.
        """
        self.client.login(username="b", password="b")

        response = self.client.get(
            reverse("event_attendance", args=[self.event_01.pk, "attend"])
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_non_ajax_attend_happy_path(self):
        # Arrange
        self.client.login(username="b", password="b")
        initial_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_01
        ).count()

        # Act
        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "attend"]),
            {"redirect_target": "/previous_view/"},
        )

        # Assert - redirects to previous view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, "/previous_view/")

        # Assert - RSVP created
        expected_rsvp_count = initial_rsvp_count + 1
        final_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_01
        ).count()
        self.assertEqual(expected_rsvp_count, final_rsvp_count)
        last_record = RSVP.objects.latest("id")
        self.assertEqual(self.event_01.id, last_record.event_id)
        self.assertEqual(self.user_01.id, last_record.user_id)

    def test_non_ajax_unattend_happy_path(self):
        # Arrange
        self.client.login(username="c", password="c")
        initial_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_02
        ).count()

        # Act
        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "unattend"]),
            {"redirect_target": "/previous_view/"},
        )
        # Assert - redirects to previous view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, "/previous_view/")

        # Assert - RSVP deleted
        expected_rsvp_count = initial_rsvp_count - 1
        final_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_02
        ).count()
        self.assertEqual(expected_rsvp_count, final_rsvp_count)
        with self.assertRaises(RSVP.DoesNotExist):
            RSVP.objects.get(event=self.event_01, user=self.user_02)

    def test_attend_RSVP_not_created_if_one_exists_for_authenticated_user(self):
        """
        manage_event_attendance does not create RSVP if one exists if action is 'attend'.

        If the user is authenticated, the request method is POST, and
        a RSVP record already exists for the authenticated user and
        target Event, then no modifications to the RSVP table should
        be performed.
        """
        self.client.login(username="c", password="c")

        initial_rsvp_count = RSVP.objects.count()
        self.client.post(reverse("event_attendance", args=[self.event_01.pk, "attend"]))

        final_rsvp_count = RSVP.objects.count()
        self.assertEqual(initial_rsvp_count, final_rsvp_count)

    def test_unattend_RSVP_table_unmodified_if_no_record_exists(self):
        """
        manage_event_attendance does not modify database if no RSVP exists and action is 'unattend'.

        The if a user is authenticated, the method is POST, and no RSVP
        record exists for the authenticated user and the target Event,
        the database should not be modified as part of the event_unattend
        view.
        """
        self.client.login(username="b", password="b")

        initial_rsvp_count = RSVP.objects.count()
        self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "unattend"])
        )

        final_rsvp_count = RSVP.objects.count()
        self.assertEqual(initial_rsvp_count, final_rsvp_count)

    def test_ajax_attend_happy_path(self):
        # Arrange
        self.client.login(username="b", password="b")
        initial_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_01
        ).count()

        # Act
        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "attend"]),
            {"redirect_target": "/previous_view/"},
            HTTP_ACCEPT="application/json",
        )

        # Assert - Response 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert - data contains "success" key True
        data = response.json()
        self.assertIn("success", data)
        self.assertTrue(data["success"])

        # Assert - RSVP record created
        expected_rsvp_count = initial_rsvp_count + 1
        final_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_01
        ).count()
        self.assertEqual(expected_rsvp_count, final_rsvp_count)

        last_record = RSVP.objects.latest("id")
        self.assertEqual(self.event_01.id, last_record.event_id)
        self.assertEqual(self.user_01.id, last_record.user_id)

    def test_ajax_unattend_happy_path(self):
        # Arrange
        self.client.login(username="c", password="c")
        initial_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_02
        ).count()

        # Act
        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "unattend"]),
            {"redirect_target": "/previous_view/"},
            HTTP_ACCEPT="application/json",
        )

        # Assert - data contains "success" key True
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("success", data)
        self.assertTrue(data["success"])

        # Assert - RSVP record deleted
        expected_rsvp_count = initial_rsvp_count - 1
        final_rsvp_count = RSVP.objects.filter(
            event=self.event_01, user=self.user_02
        ).count()
        self.assertEqual(expected_rsvp_count, final_rsvp_count)

    def test_ajax_attend_409_response_with_success_false_if_RSVP_exists(self):
        """
        AJAX attend endpoint should respond with 409 and correct data if RSVP exists

        manage_event_attendance view should return a 409 if the AJAX POST request is
        unsuccessful for the attend path in the case that there is already a matching rsvp
        record. The response content should also contain a key, "success", with a value of False.
        The content should also contain an "error_message" key.
        """
        self.client.login(username="c", password="c")

        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "attend"]),
            {"redirect_target": "/previous_view/"},
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)
        data = response.json()
        self.assertIn("success", data)
        self.assertFalse(data["success"])
        self.assertIn("error_message", data)

    def test_ajax_attend_rsvp_not_created_if_already_exists(self):
        """
        AJAX unattend endpoint should not create an RSVP record if one exists

        for a valid request to the unattend endpoint, an RSVP record not should be
        created if one aleady exists for the relevant User and Event.
        """
        self.client.login(username="c", password="c")
        initial_rsvp_count = RSVP.objects.count()

        self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "attend"]),
            {"redirect_target": "/previous_view/"},
            HTTP_ACCEPT="application/json",
        )

        expected_rsvp_count = initial_rsvp_count
        final_rsvp_count = RSVP.objects.count()
        self.assertEqual(expected_rsvp_count, final_rsvp_count)

    def test_ajax_unattend_409_response_with_success_false_if_RSVP_does_not_exist(self):
        """
        AJAX unattend endpoint should respond with 409 if no rsvp exists

        manage_event_attendance view should return a 409 if the AJAX POST request is
        unsuccessful for the unattend path in the case that there is not a matching rsvp
        record. The response content should also contain a key, "success", with a value of False.
        The content should also contain an "error_message" key.
        """
        self.client.login(username="b", password="b")

        response = self.client.post(
            reverse("event_attendance", args=[self.event_01.pk, "unattend"]),
            {"redirect_target": "/previous_view/"},
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CONFLICT)
        data = response.json()
        self.assertIn("success", data)
        self.assertFalse(data["success"])
        self.assertIn("error_message", data)

    def test_ajax_400_response_with_success_false_if_get_request(self):
        """
        AJAX manage_event_attendance should respond with 400 if requests is GET

        manage_event_attendance view should return a 400 if the AJAX request is
        GET. The response content should also contain a key, "success", with a value of
        False. The content should also contain an "error_message" key.
        """
        self.client.login(username="b", password="b")

        actions = ["unattend", "attend"]
        for action in actions:
            with self.subTest(action=action):
                response = self.client.get(
                    reverse("event_attendance", args=[self.event_01.pk, action]),
                    {"redirect_target": "/previous_view/"},
                    HTTP_ACCEPT="application/json",
                )

                self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
                data = response.json()
                self.assertIn("success", data)
                self.assertFalse(data["success"])
                self.assertIn("error_message", data)

    def test_ajax_403_response_with_success_false_if_not_authenticated(self):
        """
        AJAX manage_event_attendance should respond with 403 if no authenticated user

        manage_event_attendance view should return a 403 if the user is not authenticated.
        The response content should also contain a key, "success", with a value of
        False. The content should also contain an "error_message" key.
        """
        actions = ["unattend", "attend"]
        for action in actions:
            with self.subTest(action=action):
                response = self.client.post(
                    reverse("event_attendance", args=[self.event_01.pk, action]),
                    {"redirect_target": "/previous_view/"},
                    HTTP_ACCEPT="application/json",
                )

                self.assertEqual(response.status_code, 403)
                data = response.json()
                self.assertIn("success", data)
                self.assertFalse(data["success"])
                self.assertIn("error_message", data)
