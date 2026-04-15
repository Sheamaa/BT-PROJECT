from django.urls import path
from . import views

urlpatterns = [
    path('', views.auth_page, name='auth_page'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('hospital-volunteering/', views.hospital_volunteering, name='hospital_volunteering'),
    path('workshops/', views.workshops, name='workshops'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/mark-read/', views.mark_all_read, name='mark_all_read'),
    path('apply/', views.apply, name='apply'),
    path('recommendation/', views.recommendation, name='recommendation'),
    path('workshops/', views.workshops, name='workshops'),
    path('workshops/register/<int:workshop_id>/', views.register_workshop, name='register_workshop'),
]