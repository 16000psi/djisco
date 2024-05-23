import random

from django.core.management.base import BaseCommand

from events.models import (
    RSVP,
    ContributionCommitment,
    ContributionItem,
    ContributionRequirement,
    Event,
)
from users.models import User

from .dummy_data.contribution_item_data import contribution_item_data
from .dummy_data.events_data import events_data
from .dummy_data.users_data import users_data


class Command(BaseCommand):
    help = "Add dummy data to the database"

    def handle(self, *args, **kwargs):
        # Find and delete users by username or email
        usernames = [user_data["username"] for user_data in users_data]
        emails = [user_data["email"] for user_data in users_data]
        User.objects.filter(username__in=usernames).delete()
        User.objects.filter(email__in=emails).delete()

        # Generate users
        users = []
        for user_data in users_data:
            user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
            )
            user.profile.bio = user_data["bio"]
            user.profile.location = user_data["location"]
            user.profile.save()
            users.append(user)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created user {user.username} with profile"
                )
            )

        # Find and delete all dummy contribution items
        contribution_item_titles = [
            contribution_item["title"] for contribution_item in contribution_item_data
        ]

        ContributionItem.objects.filter(title__in=contribution_item_titles).delete()

        contribution_items = []

        # Generate contribution items
        for contribution_item in contribution_item_data:
            item = ContributionItem.objects.create(title=contribution_item["title"])
            contribution_items.append(item)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created contribution_item {item.title}"
                )
            )

        # Generate events
        for i, event_data in enumerate(events_data):
            user = User.objects.get(username=usernames[i % len(usernames)])
            event = Event.objects.create(
                title=event_data["title"],
                maximum_attendees=event_data["maximum_attendees"],
                starts_at=event_data["starts_at"],
                ends_at=event_data["ends_at"],
                location=event_data["location"],
                description=event_data["description"],
                organiser=user,
                contact=user,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created event {event.title} with organiser {user.username}"
                )
            )

            # Generate RSVPS for event
            users_without_organiser = users[:]
            users_without_organiser.remove(user)
            rsvps_to_create = random.randint(1, 4)
            selected_users = random.sample(users_without_organiser, rsvps_to_create)
            event_rsvps = []
            for selected_user in selected_users:
                rsvp = RSVP.objects.create(user=selected_user, event=event)
                event_rsvps.append(rsvp)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {rsvps_to_create} RSVPs for event {event.title}"
                )
            )

            # Create requirements and corresponding commitments for event
            num_items_to_select = random.randint(2, 7)
            selected_items = random.sample(contribution_items, num_items_to_select)
            for item in selected_items:
                num_requirements_to_create = random.randint(1, 5)
                for _ in range(num_requirements_to_create):
                    requirement = ContributionRequirement.objects.create(
                        contribution_item=item, event=event
                    )
                    if random.random() < 2 / 3:
                        ContributionCommitment.objects.create(
                            contribution_requirement=requirement,
                            RSVP=random.choice(event_rsvps),
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created requirements for {num_items_to_select} items for event {event.title}"
                )
            )
