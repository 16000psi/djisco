from django.test import TestCase

from users.models import Profile, User


class ProfileSignalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_profile_creation(self):
        """Test that a Profile instance is created for a new user."""
        self.assertTrue(
            Profile.objects.filter(user=self.user).exists(),
            "Profile should be created for new users.",
        )

    def test_profile_update(self):
        """Test that the Profile instance is updated when the user is updated."""

        # Act - update user
        self.user.first_name = "UpdatedName"
        self.user.save()

        # Assert - profile still exists
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

        # Act - update profile record
        profile = Profile.objects.get(user=self.user)
        bio_text = "Updated bio"
        profile.bio = bio_text
        profile.save()

        # Assert - change took effect
        updated_profile = Profile.objects.get(user=self.user)
        self.assertEqual(
            updated_profile.bio, bio_text, "Profile bio should be updated."
        )
