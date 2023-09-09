from django.urls import path

from . import views

urlpatterns = [
    path("join_room/", views.index, name="index"),
    path('registration/',views.registration.as_view()),
    path('login/',views.logins.as_view()),
    path('logout/',views.logouts.as_view()),
    path("room/<str:room_name>/", views.room, name="room"),
    path("private_room/<int:user_1>@<int:user_2>/", views.private_room, name="private_room")
]