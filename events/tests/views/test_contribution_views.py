from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import (
    RSVP,
    ContributionCommitment,
    ContributionItem,
    ContributionRequirement,
    Event,
)
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
            "Unauthorised to modify event requirements", response.content.decode()
        )

    def test_get_method_not_allowed(self):
        self.client.force_login(self.new_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_happy_path_new_contribution_item(self):
        # Arrange
        self.client.force_login(self.new_user)
        initial_contribution_item_count = ContributionItem.objects.count()
        initial_contribution_requirement_count = ContributionRequirement.objects.count()

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
        initial_contribution_item_count = ContributionItem.objects.count()
        initial_contribution_requirement_count = ContributionRequirement.objects.count()

        # Act
        response = self.client.post(self.url, self.requirement_data)

        # Assert - Redirects to detail view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # self.assertRedirects(response, reverse("event_detail", args=[1]))

        # Assert - ContributionItem not created
        final_contribution_item_count = ContributionItem.objects.count()
        self.assertEqual(initial_contribution_item_count, final_contribution_item_count)

        # Assert - Correct ContributionRequirements created
        new_contribution_requirement_count = ContributionRequirement.objects.count()
        # - Number of new requirements equal to quantity
        self.assertEqual(
            initial_contribution_requirement_count + self.requirement_data["quantity"],
            new_contribution_requirement_count,
        )
        contribution_requirements = ContributionRequirement.objects.all()
        # - All new requirements point to the already existing ContributionItem record
        for instance in contribution_requirements:
            self.assertEqual(instance.contribution_item, previously_existing_item)


class CommitmentCreateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.new_user = User.objects.create_user(username="b", password="b")
        cls.user_not_attending = User.objects.create_user(username="c", password="c")
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
        cls.rsvp = RSVP.objects.create(user=cls.new_user, event=cls.event)
        cls.contribution_item = ContributionItem.objects.create(title="test_example")
        cls.url = reverse(
            "commitment_create", args=[cls.event.pk, cls.contribution_item.pk]
        )
        contribution_requirements = [
            ContributionRequirement(
                event=cls.event, contribution_item=cls.contribution_item
            )
            for _ in range(5)
        ]
        ContributionRequirement.objects.bulk_create(contribution_requirements)
        cls.commitment_data = {
            "quantity": 3,
        }

    def test_forbidden_for_unauthenticated_user(self):
        response = self.client.post(self.url, self.commitment_data)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertIn(
            "Unauthorised to modify event requirements", response.content.decode()
        )

    def test_get_request_happy_path(self):
        # Arrange
        self.client.force_login(self.new_user)

        # Act
        response = self.client.get(self.url)

        # Assert - response 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Assert - the context contains the expected forms and objects
        self.assertIn("form", response.context)
        self.assertEqual(response.context["event"], self.event)

    def test_post_request_no_change_if_all_requirements_fulfilled(self):
        # Arrange
        self.client.force_login(self.new_user)
        unfulfilled_requirements = ContributionRequirement.objects.exclude(
            contributioncommitment__isnull=False
        )
        # - fulfill all requirements
        for requirement in unfulfilled_requirements:
            ContributionCommitment.objects.create(
                RSVP=self.rsvp, contribution_requirement=requirement
            )
        initial_commitment_count = ContributionCommitment.objects.count()

        # Act
        self.client.post(self.url, {"quantity": 1})

        # Assert - no more commitments created
        final_commitment_count = ContributionCommitment.objects.count()
        self.assertEqual(initial_commitment_count, final_commitment_count)

    def test_post_request_400_if_quantity_greater_than_available(self):
        # Arrange
        self.client.force_login(self.new_user)

        # Act
        response = self.client.post(self.url, {"quantity": 7})

        # Assert - 400 response
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_post_request_forbidden_if_no_rsvp(self):
        # Arrange
        self.client.force_login(self.user_not_attending)
        initial_commitment_count = ContributionCommitment.objects.count()

        # Act
        response = self.client.post(self.url, self.commitment_data)

        # Assert - Redirects to detail view
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        # Assert - no commitments created
        final_commitment_count = ContributionCommitment.objects.count()
        self.assertEqual(initial_commitment_count, final_commitment_count)

    def test_post_request_happy_path(self):
        # Arrange
        self.client.force_login(self.new_user)
        previously_existing_commitments_count = ContributionCommitment.objects.count()

        # Act
        response = self.client.post(self.url, self.commitment_data)

        # Assert - Redirects to detail view
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("event_detail", args=[1]))

        # Assert - Creates correct number of new ContributionCommitments
        new_commitments_count = ContributionCommitment.objects.count()
        self.assertEqual(
            previously_existing_commitments_count + self.commitment_data["quantity"],
            new_commitments_count,
        )

        # Assert - Each new commitment points to a requirement which
        # points to the correct ContributionItem
        new_commitments = ContributionCommitment.objects.prefetch_related(
            "contribution_requirement"
        ).all()
        for commitment in new_commitments:
            requirement = commitment.contribution_requirement
            self.assertEqual(requirement.contribution_item, self.contribution_item)
