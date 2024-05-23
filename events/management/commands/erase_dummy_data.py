from django.core.management.base import BaseCommand

from events.models import ContributionItem
from users.models import User

from .dummy_data.contribution_item_data import contribution_item_data
from .dummy_data.users_data import users_data


class Command(BaseCommand):
    help = "Erase all dummy data"

    def handle(self, *args, **kwargs):
        # Find and delete users by username or email
        usernames = [user_data["username"] for user_data in users_data]
        emails = [user_data["email"] for user_data in users_data]
        User.objects.filter(username__in=usernames).delete()
        User.objects.filter(email__in=emails).delete()

        # Find and delete all dummy contribution items
        contribution_item_titles = [
            contribution_item["title"] for contribution_item in contribution_item_data
        ]

        ContributionItem.objects.filter(title__in=contribution_item_titles).delete()

        self.stdout.write(
            self.style.SUCCESS("Successfully removed dummy data from database")
        )
