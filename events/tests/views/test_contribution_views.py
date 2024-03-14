from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import ContributionItem, ContributionRequirement, Event
from users.models import User


class RequirmentCreateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create_user(username="b", password="b")
        cls.event = Event.objects.create(
            title="event01",
            organiser=cls.new_user,
            contact=cls.new_user,
            starts_at=timezone.now() + timezone.timedelta(hours=1),
            ends_at=timezone.now() + timezone.timedelta(hours=2),
            location="here",
            description="brillientay",
            maximum_attendees=20,
        )
        cls.url = reverse("requirement_create", args=[cls.event.pk])
        cls.requirement_data = {
            "contribution_item": "test_example",
            "quantity": 5,
        }

    def test_forbidden_for_unauthenticated_user(self):
        response = self.client.post(self.url, self.requirement_data)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn(
            "Unauthorised to modify Event attendance", response.content.decode()
        )

    def test_get_method_not_allowed(self):
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_happy_path_new_contribution_item(self):
        # Arrange
        self.client.force_login(self.new_user)
        initial_contribution_item_count = ContributionItem.objects.all().count()
        initial_contribution_requirement_count = (
            ContributionRequirement.objects.all().count()
        )

        # Act
        response = self.client.post(self.url, self.requirement_data)

        # Assert - Redirects to detail view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("event_detail", args=[1]))

        # Assert - ContributionItem Created
        final_contribution_item_count = ContributionItem.objects.all().count()
        new_contribution_item_name = ContributionItem.objects.first().title
        self.assertEqual(
            initial_contribution_item_count + 1, final_contribution_item_count
        )
        self.assertEqual(
            self.requirement_data["contribution_item"], new_contribution_item_name
        )

        # Assert - Correct ContributionRequirements created
        new_contribution_requirement_count = (
            ContributionRequirement.objects.all().count()
        )
        # - Number of new requirements equal to quantity
        self.assertEqual(
            initial_contribution_requirement_count + self.requirement_data["quantity"],
            new_contribution_requirement_count,
        )
        created_item = ContributionItem.objects.first()
        contribution_requirements = ContributionRequirement.objects.all()
        # - All new requirements point to the new ContributionItem record
        for instance in contribution_requirements:
            self.assertEqual(instance.contribution_item, created_item)

    def test_happy_path_existing_contribution_item(self):
        # Arrange
        self.client.force_login(self.new_user)
        # - Create ContributionItem, mimic it already existing in the database
        ContributionItem.objects.create(
            title=self.requirement_data["contribution_item"]
        )
        previously_existing_item = ContributionItem.objects.first()
        initial_contribution_item_count = ContributionItem.objects.all().count()
        initial_contribution_requirement_count = (
            ContributionRequirement.objects.all().count()
        )

        # Act
        response = self.client.post(self.url, self.requirement_data)

        # Assert - Redirects to detail view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("event_detail", args=[1]))

        # Assert - ContributionItem not created
        final_contribution_item_count = ContributionItem.objects.all().count()
        self.assertEqual(initial_contribution_item_count, final_contribution_item_count)

        # Assert - Correct ContributionRequirements created
        new_contribution_requirement_count = (
            ContributionRequirement.objects.all().count()
        )
        # - Number of new requirements equal to quantity
        self.assertEqual(
            initial_contribution_requirement_count + self.requirement_data["quantity"],
            new_contribution_requirement_count,
        )
        contribution_requirements = ContributionRequirement.objects.all()
        # - All new requirements point to the already existing ContributionItem record
        for instance in contribution_requirements:
            self.assertEqual(instance.contribution_item, previously_existing_item)
