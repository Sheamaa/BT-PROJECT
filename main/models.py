from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='main_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='main_user_set',
        blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    qid = models.CharField(max_length=12)
    qid_expiry_date = models.DateField(null=True, blank=True)
    academic_level = models.CharField(max_length=100)
    grade_year = models.CharField(max_length=20, blank=True, null=True)
    institution = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    id_document = models.FileField(upload_to='profile_documents/', null=True, blank=True)

    def __str__(self):
        return self.full_name


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    full_name = models.CharField(max_length=150)
    ACCESS_LEVEL_CHOICES = [
        ('admin', 'Admin'),
        ('coordinator', 'Coordinator'),
    ]
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES)

    def __str__(self):
        return self.full_name


class Department(models.Model):
    ELIGIBILITY_CHOICES = [
    ('highschool', 'High School'),
    ('undergraduate', 'Undergraduate'),
    ]
    AREA_CHOICES = [
        ('doha', 'Doha'),
        ('alwakra', 'Al Wakra'),
        ('alkhor', 'Al Khor'),
        ('dukhan', 'Dukhan'),
    ]
    area = models.CharField(max_length=20, choices=AREA_CHOICES, default='doha')
    has_evening_shift = models.BooleanField(default=False)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    timings = models.CharField(max_length=50)
    supervisor = models.CharField(max_length=150)
    eligibility = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES, default='undergraduate')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DepartmentWeeklySlot(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='weekly_slots')
    week_start_date = models.DateField()
    total_slots = models.IntegerField()
    filled_slots = models.IntegerField(default=0)

    def is_full(self):
        return self.filled_slots >= self.total_slots

    def __str__(self):
        return f"{self.department.name} - {self.week_start_date}"


class Application(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    first_choice_dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='first_choice_applications')
    second_choice_dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='second_choice_applications')
    preferred_slot = models.ForeignKey(DepartmentWeeklySlot, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(default=5)
    approved_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_applications')

    def __str__(self):
        return f"Application by {self.student.full_name} - {self.status}"


class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='application_documents/')
    document_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} - {self.application}"


class Recommendation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='recommendations')
    suggested_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    answers = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.student.full_name}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('application_submitted', 'Application Submitted'),
        ('application_approved', 'Application Approved'),
        ('application_rejected', 'Application Rejected'),
        ('general', 'General'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


class Workshop(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    timings = models.CharField(max_length=50)
    description = models.TextField()
    poster = models.ImageField(upload_to='workshop_posters/')
    picture = models.ImageField(upload_to='workshop_pictures/', null=True, blank=True)
    capacity = models.IntegerField()

    def __str__(self):
        return self.name


class WorkshopRegistration(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='workshop_registrations')
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')

    def __str__(self):
        return f"{self.student.full_name} - {self.workshop.name}"


class VolunteeringDocument(models.Model):
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='volunteering_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name}"


class AttendanceSheet(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='attendance_sheet')
    file = models.FileField(upload_to='attendance_sheets/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    staff_note = models.TextField(null=True, blank=True)
    def __str__(self):
       return f"Attendance - {self.application.student.full_name}"

class Certificate(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('workshop', 'Workshop'),
        ('hospital', 'Hospital Volunteering'),
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certificates')
    application = models.OneToOneField(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificate')
    workshop_registration = models.OneToOneField(WorkshopRegistration, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificate')
    department_name = models.CharField(max_length=100)
    start_date = models.DateField()
    hours = models.IntegerField()
    certificate_file = models.FileField(upload_to='certificates/')
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate - {self.student.full_name}"
    

# class Feedback(models.Model):
#     application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='feedback')
#     feedback = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     def __str__(self):
#         return f"Feedback - {self.application.student.full_name}"
