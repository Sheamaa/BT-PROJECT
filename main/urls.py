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
    # Staff URLs
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/application/<int:app_id>/', views.staff_application_detail, name='staff_application_detail'),
    path('staff/application/<int:app_id>/approve/', views.approve_application, name='approve_application'),
    path('staff/application/<int:app_id>/reject/', views.reject_application, name='reject_application'),
    path('staff/workshops/', views.staff_workshops, name='staff_workshops'),
    path('staff/workshops/add/', views.staff_workshop_add, name='staff_workshop_add'),
    path('staff/workshops/<int:workshop_id>/edit/', views.staff_workshop_edit, name='staff_workshop_edit'),
    path('staff/workshops/<int:workshop_id>/delete/', views.staff_workshop_delete, name='staff_workshop_delete'),
    path('staff/departments/', views.staff_departments, name='staff_departments'),
    path('staff/departments/add/', views.staff_department_add, name='staff_department_add'),
    path('staff/departments/<int:dept_id>/edit/', views.staff_department_edit, name='staff_department_edit'),
    path('staff/departments/<int:dept_id>/delete/', views.staff_department_delete, name='staff_department_delete'),
]