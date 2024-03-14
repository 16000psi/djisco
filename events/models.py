from django.db import models
from django.db.models import BooleanField, Case, Count, F, Q, Value, When
from django.db.models.functions import Greatest
from django.utils import timezone

from users.models import User


class EventQuerySet(models.QuerySet):
    def for_user(self, user):
        subquery = RSVP.objects.filter(user=user).values("event_id")
        return self.filter(id__in=models.Subquery(subquery))

    def with_attendance_fields(self):
        return self.annotate(
            attendee_count=Count("respondents"),
            remaining_spaces=Greatest(
                F("maximum_attendees") - F("attendee_count"),
                0,
            ),
        )

    def with_has_user_rsvp(self, user):
        subquery = RSVP.objects.filter(user=user).values("event_id")
        return self.annotate(
            has_user_rsvp=Case(
                When(id__in=models.Subquery(subquery), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def in_future(self):
        return self.filter(ends_at__gt=timezone.now())

    def in_past(self):
        return self.filter(ends_at__lte=timezone.now())


class EventManager(models.Manager):
    def get_queryset(self):
        return EventQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def with_attendance_fields(self):
        return self.get_queryset().with_attendance_fields()

    def with_has_user_rsvp(self, user):
        return self.get_queryset().with_has_user_rsvp(user)

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
    contact = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="is_contact"
    )
    maximum_attendees = models.IntegerField()
    respondents = models.ManyToManyField(User, through="RSVP")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.TextField(max_length=400)
    description = models.TextField(max_length=2000, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(ends_at__gt=models.F("starts_at")),
                name="end_datetime_after_start_datetime",
            )
        ]

    @property
    def accepting_attendees(self):
        remaining_spaces = max(self.maximum_attendees - self.get_attendee_count(), 0)

        return self.ends_at > timezone.now() and remaining_spaces > 0

    def get_attendees(self):
        subquery = RSVP.objects.filter(event=self).values("user_id")
        return User.objects.filter(id__in=models.Subquery(subquery))

    def get_contribution_requirements(self):
        return ContributionRequirement.objects.filter(event=self)

    def get_attendee_count(self):
        return RSVP.objects.filter(event=self).count()

    def __str__(self):
        return f"{self.title}, {self.starts_at} - {self.ends_at}"


class RSVP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "event")]

    def __str__(self):
        return f"Attending {self.event.title}"


class ContributionItemQuerySet(models.QuerySet):
    def filter_for_event(self, event):
        subquery = ContributionRequirement.objects.filter(event=event).values(
            "contribution_item_id"
        )
        return self.filter(id__in=models.Subquery(subquery))

    def with_counts_for_event(self, event):
        return self.annotate(
            requirements_count=Count(
                "contributionrequirement",
                filter=Q(contributionrequirement__event=event),
                distinct=True,
            ),
            commitments_count=Count(
                "contributionrequirement__contributioncommitment",
                filter=Q(contributionrequirement__event=event),
            ),
        )


class ContributionItem(models.Model):
    objects = ContributionItemQuerySet.as_manager()
    title = models.TextField(unique=True)

    def __str__(self):
        return f"{self.pk} - {self.title}"


class ContributionRequirementQuerySet(models.QuerySet):
    def get_unfulfilled_requirements_for_item_for_event(self, contribution_item, event):
        return self.filter(
            contribution_item=contribution_item, event=event
        ).exclude(contributioncommitment__isnull=False)


class ContributionRequirement(models.Model):
    objects = ContributionRequirementQuerySet.as_manager()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    contribution_item = models.ForeignKey(ContributionItem, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.pk} - {self.contribution_item.title}"


class ContributionCommitment(models.Model):
    RSVP = models.ForeignKey(RSVP, on_delete=models.CASCADE)
    contribution_requirement = models.ForeignKey(
        ContributionRequirement, on_delete=models.RESTRICT
    )

    def __str__(self):
        return f"{self.RSVP.user} bringing {self.contribution_requirement}"
