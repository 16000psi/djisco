from django.db import models
from django.utils import timezone


class TimeFilterOptions:
    """
    Used by EventListView to determine the view title, queryset
    orderfing and filtering.

    returns:
    (string for view title, string used in qs "order_by", qs filter)
    """

    @classmethod
    def get_option(cls, when) -> tuple[str, str, models.Q]:
        if when == "future":
            return cls.future
        elif when == "past":
            return cls.past
        elif when == "all":
            return cls.all
        else:
            raise ValueError

    @classmethod
    @property
    def all(cls):
        return ("All Events", "-attendee_count", models.Q())

    @classmethod
    @property
    def past(cls):
        return ("Past Events", "-ends_at", models.Q(ends_at__lte=timezone.now()))

    @classmethod
    @property
    def future(cls):
        return ("Events", "ends_at", models.Q(ends_at__gt=timezone.now()))
