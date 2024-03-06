# Register your models here.
from django.contrib import admin

from .models import (
    RSVP,
    ContributionCommitment,
    ContributionItem,
    ContributionRequirement,
    Event,
)

admin.site.register(Event)
admin.site.register(RSVP)
admin.site.register(ContributionRequirement)
admin.site.register(ContributionCommitment)
admin.site.register(ContributionItem)
