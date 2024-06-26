from django.urls import include, path, register_converter

from . import converters, views

register_converter(converters.WhenConverter, "when")

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("signup/", views.signup_view, name="signup"),
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("", views.home_view, name="home"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path(
        "events/<int:pk>/contributions/",
        views.EventDetailContributionsView.as_view(),
        name="event_detail_contributions",
    ),
    path(
        "events/<when:when>/<int:page>/",
        views.EventListView.as_view(),
        name="event_list",
    ),
    path(
        "events/<int:pk>/attendance/<str:action>/",
        views.manage_event_attendance,
        name="event_attendance",
    ),
    path(
        "events/new/",
        views.EventCreateView.as_view(
            extra_context={"title": "Create Event", "submit_text": "Create new event"}
        ),
        name="event_new",
    ),
    path(
        "events/<int:pk>/edit/",
        views.EventUpdateView.as_view(
            extra_context={
                "title": "Update Event",
                "submit_text": "Save changes to event",
            }
        ),
        name="event_edit",
    ),
    path(
        "events/<int:pk>/delete/",
        views.EventDeleteView.as_view(),
        name="event_delete",
    ),
    path(
        "events/<int:pk>/requirements/new",
        views.requirement_create_view,
        name="requirement_create",
    ),
    path(
        "events/<int:pk>/requirements/<int:contribution_item_pk>/edit",
        views.requirement_edit_view,
        name="requirement_edit",
    ),
    path(
        "events/<int:pk>/<int:contribution_item_pk>/commitment",
        views.commitment_create_view,
        name="commitment_create",
    ),
]
