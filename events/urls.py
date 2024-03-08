from django.urls import include, path

from . import views

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<str:when>/<int:page>/", views.event_list, name="event_list"),
    path(
        "events/<int:pk>/attendance/<str:action>/",
        views.manage_event_attendance,
        name="event_attendance",
    ),
    path("events/new/", views.event_create_view, name="event_new"),
    path("events/<int:pk>/edit/", views.event_update_view, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete_view, name="event_delete"),
]
