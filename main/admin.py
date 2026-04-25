from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, StudentProfile, StaffProfile, Department,
    DepartmentWeeklySlot, Application, ApplicationDocument,
    Recommendation, Notification, Workshop, WorkshopRegistration, VolunteeringDocument, AttendanceSheet, WorkshopAttendanceSheet, Certificate
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'academic_level', 'institution', 'phone']

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'access_level']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'supervisor', 'timings', 'total_slots', 'is_active']

@admin.register(DepartmentWeeklySlot)
class DepartmentWeeklySlotAdmin(admin.ModelAdmin):
    list_display = ['department', 'week_start_date', 'filled_slots']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'first_choice_dept', 'second_choice_dept', 'status', 'submitted_at']
    list_filter = ['status']

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'application', 'uploaded_at']

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['student', 'suggested_department', 'created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'is_read', 'created_at']

@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'capacity']

@admin.register(WorkshopRegistration)
class WorkshopRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'workshop', 'status', 'registered_at']

@admin.register(AttendanceSheet)
class AttendanceSheetAdmin(admin.ModelAdmin):
    list_display = ['application', 'status', 'uploaded_at']

@admin.register(VolunteeringDocument)
class VolunteeringDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'uploaded_at']

@admin.register(WorkshopAttendanceSheet)
class WorkshopAttendanceSheetAdmin(admin.ModelAdmin):
    list_display = ['registration', 'status', 'uploaded_at']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['student', 'department_name', 'start_date', 'hours']