from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.models import User


class EventQuerySet(models.QuerySet):
    def for_user(self, user):
        subquery = RSVP.objects.filter(
            user=user, status=RSVP.AttendanceOptions.YES
        ).values("event_id")
        return self.filter(id__in=models.Subquery(subquery))

    def in_future(self):
        return self.filter(ends_at__gt=timezone.now())

    def in_past(self):
        return self.filter(ends_at__lte=timezone.now())


class EventManager(models.Manager):
    def get_queryset(self):
        return EventQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def in_future(self):
        return self.get_queryset().in_future()

    def in_past(self):
        return self.get_queryset().in_past()


class Event(models.Model):
    objects = EventManager()
    title = models.CharField(max_length=200)
    organiser = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="is_organising"
    )
    respondents = models.ManyToManyField(User, through="RSVP")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.TextField(max_length=400)
    description = models.TextField(max_length=2000, blank=True)

    def get_attendees(self):
        subquery = RSVP.objects.filter(
            event=self, status=RSVP.AttendanceOptions.YES
        ).values("user_id")
        return User.objects.filter(id__in=models.Subquery(subquery))

    def get_contribution_requirements(self):
        return ContributionRequirement.objects.filter(event=self)

    def get_attendee_count(self):
        return RSVP.objects.filter(
            event=self, status=RSVP.AttendanceOptions.YES
        ).count()

    def __str__(self):
        return f"{self.title}, {self.starts_at} - {self.ends_at}"


class RSVP(models.Model):
    class AttendanceOptions(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.TextField(
        choices=AttendanceOptions.choices, default=AttendanceOptions.YES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status


class ContributionRequirement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    title = models.TextField()

    def __str__(self):
        return self.title


class ContributionCommitment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    contribution_requirement = models.ForeignKey(
        ContributionRequirement, on_delete=models.RESTRICT, null=True
    )

    def __str__(self):
        return f"{self.user} bringing {self.title}"
