from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, StudentProfile, Workshop, Department, Recommendation, DepartmentWeeklySlot, ApplicationDocument, Application, Notification, Workshop, WorkshopRegistration
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .decision_tree import get_recommendation


from functools import wraps
from django.shortcuts import get_object_or_404


def auth_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'auth.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    return redirect('auth_page')

def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        academic_level = request.POST.get('academic_level')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('auth_page')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role='student'
        )
        StudentProfile.objects.create(
            user=user,
            full_name=full_name,
            academic_level=academic_level,
            institution='',
            phone=''
        )
        login(request, user)
        return redirect('dashboard')
    return redirect('auth_page')


@login_required
def profile_view(request):
    profile = request.user.student_profile

    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name')
        profile.date_of_birth = request.POST.get('date_of_birth') or None
        profile.phone = request.POST.get('phone')
        profile.qid = request.POST.get('qid')
        profile.qid_expiry_date = request.POST.get('qid_expiry_date') or None
        profile.academic_level = request.POST.get('academic_level') or None
        profile.grade_year = request.POST.get('grade_year')
        profile.institution = request.POST.get('institution')

        if request.FILES.get('id_document'):
            profile.id_document = request.FILES['id_document']

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'profile.html', {'profile': profile})


@login_required
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def dashboard(request):
    try:
        profile = request.user.student_profile
        applications = profile.applications.all().order_by('-submitted_at')
    except:
        profile = None
        applications = []

    return render(request, 'dashboard.html', {
        'profile': profile,
        'applications': applications,
    })


@login_required
def hospital_volunteering(request):
    highschool_depts = Department.objects.filter(
        is_active=True,
        eligibility__in=['highschool']
    )
    undergraduate_depts = Department.objects.filter(
        is_active=True,
        eligibility__in=['undergraduate']
    )
    return render(request, 'hospital_volunteering.html', {
        'highschool_depts': highschool_depts,
        'undergraduate_depts': undergraduate_depts,
    })

@login_required
def apply(request):
    profile = request.user.student_profile
    academic_level = profile.academic_level

    # filter departments based on academic level
    if academic_level == 'high-school':
        departments = Department.objects.filter(
            eligibility='highschool',
            is_active=True
        )
    else:
        departments = Department.objects.filter(
            is_active=True
        )

    if request.method == 'POST':
        first_choice_id = request.POST.get('first_choice_dept')
        second_choice_id = request.POST.get('second_choice_dept')
        preferred_week = request.POST.get('preferred_week')

        # validate that first choice is selected
        if not first_choice_id:
            messages.error(request, 'Please select a first choice department.')
            return redirect('apply')

        # validate preferred week is a Sunday
        if preferred_week:
            week_date = date.fromisoformat(preferred_week)
            if week_date.weekday() != 6:
                messages.error(request, 'Please select a Sunday as your week start date.')
                return redirect('apply')
        else:
            messages.error(request, 'Please select a preferred week.')
            return redirect('apply')

        # check if student already has an active application
        active_application = Application.objects.filter(
            student=profile,
            status__in=['submitted', 'under_review', 'approved']
        ).first()

        if active_application:
            messages.error(request, 'You already have an active application. You cannot submit another one until it is resolved.')
            return redirect('dashboard')

        # get or create the weekly slot
        first_dept = Department.objects.get(id=first_choice_id)
        slot, created = DepartmentWeeklySlot.objects.get_or_create(
            department=first_dept,
            week_start_date=week_date,
            defaults={
                'total_slots': 5,
                'filled_slots': 0
            }
        )

        # check if slot is full
        if slot.is_full():
            messages.error(request, 'Sorry, this department is full for the selected week. Please choose another week or department.')
            return redirect('apply')

        # create the application
        application = Application.objects.create(
            student=profile,
            first_choice_dept=first_dept,
            second_choice_dept=Department.objects.get(id=second_choice_id) if second_choice_id else None,
            preferred_slot=slot,
            status='submitted'
        )

        # handle additional documents
        for file in request.FILES.getlist('extra_documents'):
            ApplicationDocument.objects.create(
                application=application,
                file=file,
                document_type='additional'
            )

        # create notification for student
        Notification.objects.create(
            user=request.user,
            message=f'Your application to {first_dept.name} has been submitted successfully and is under review.',
            type='application_submitted'
        )

        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('dashboard')

    return render(request, 'apply.html', {
        'profile': profile,
        'departments': departments,
    })

@login_required
def recommendation(request):
    return render(request, 'recommendation.html')


@login_required
def recommendation(request):
    recommended_dept = None

    if request.method == 'POST':
        answers = {
            'willing_to_travel': request.POST.get('willing_to_travel'),
            'prior_experience': request.POST.get('prior_experience'),
            'stress_tolerance': request.POST.get('stress_tolerance'),
            'patient_interaction': request.POST.get('patient_interaction'),
            'preference': request.POST.get('preference'),
            'emergency_interest': request.POST.get('emergency_interest'),
            'work_type': request.POST.get('work_type'),
        }

        student_area = request.POST.get('area', 'doha')
        academic_level = request.user.student_profile.academic_level

        recommended_dept = get_recommendation(
            answers, academic_level, student_area
        )

        # Save recommendation to database
        Recommendation.objects.create(
            student=request.user.student_profile,
            suggested_department=recommended_dept,
            answers=answers
        )

    return render(request, 'recommendation.html', {
        'recommended_dept': recommended_dept,
    })

@login_required
def register_workshop(request, workshop_id):
    if request.method == 'POST':
        workshop = Workshop.objects.get(id=workshop_id)
        profile = request.user.student_profile

        already_registered = WorkshopRegistration.objects.filter(
            student=profile,
            workshop=workshop,
            status='registered'
        ).exists()

        if already_registered:
            messages.error(request, 'You are already registered for this workshop.')
            return redirect('workshops')

        if workshop.capacity <= 0:
            messages.error(request, 'Sorry this workshop is full.')
            return redirect('workshops')

        WorkshopRegistration.objects.create(
            student=profile,
            workshop=workshop,
            status='registered'
        )

        workshop.capacity -= 1
        workshop.save()

        Notification.objects.create(
            user=request.user,
            message=f'You have successfully registered for {workshop.name}.',
            type='general'
        )

        messages.success(request, f'You have successfully registered for {workshop.name}!')
        return redirect('workshops')


# STAFF VIEWS



def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'staff':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@staff_required
def staff_dashboard(request):
    status_filter = request.GET.get('status', 'all')

    applications = Application.objects.all().order_by('-submitted_at')

    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    total = Application.objects.count()
    pending = Application.objects.filter(status='submitted').count()
    under_review = Application.objects.filter(status='under_review').count()
    approved = Application.objects.filter(status='approved').count()
    rejected = Application.objects.filter(status='rejected').count()

    return render(request, 'staff/staff_dashboard.html', {
        'applications': applications,
        'status_filter': status_filter,
        'total': total,
        'pending': pending,
        'under_review': under_review,
        'approved': approved,
        'rejected': rejected,
    })

@login_required
@staff_required
def staff_application_detail(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    return render(request, 'staff/application_detail.html', {
        'application': application,
    })

@login_required
@staff_required
def approve_application(request, app_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=app_id)
        application.status = 'approved'
        application.save()

        slot = application.preferred_slot
        if slot:
            slot.filled_slots += 1
            slot.save()

        Notification.objects.create(
            user=application.student.user,
            message=f'Congratulations! Your application to {application.first_choice_dept.name} has been approved.',
            type='application_approved'
        )

        messages.success(request, f'Application by {application.student.full_name} has been approved.')
        return redirect('staff_dashboard')

@login_required
@staff_required
def reject_application(request, app_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=app_id)
        reason = request.POST.get('reason', 'No reason provided.')
        application.status = 'rejected'
        application.save()

        Notification.objects.create(
            user=application.student.user,
            message=f'Your application to {application.first_choice_dept.name} has been rejected. Reason: {reason}',
            type='application_rejected'
        )

        messages.success(request, f'Application by {application.student.full_name} has been rejected.')
        return redirect('staff_dashboard')


@login_required
@staff_required
def staff_workshops(request):
    workshops = Workshop.objects.all().order_by('-start_date')
    return render(request, 'staff/staff_workshops.html', {
        'workshops': workshops,
    })

@login_required
@staff_required
def staff_workshop_add(request):
    if request.method == 'POST':
        Workshop.objects.create(
            name=request.POST.get('name'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            timings=request.POST.get('timings'),
            description=request.POST.get('description'),
            capacity=request.POST.get('capacity'),
            picture=request.FILES.get('picture'),
            poster=request.FILES.get('poster'),
        )
        messages.success(request, 'Workshop added successfully!')
        return redirect('staff_workshops')
    return render(request, 'staff/staff_workshop_form.html', {
        'action': 'Add',
        'workshop': None,
    })

@login_required
@staff_required
def staff_workshop_edit(request, workshop_id):
    workshop = get_object_or_404(Workshop, id=workshop_id)
    if request.method == 'POST':
        workshop.name = request.POST.get('name')
        workshop.start_date = request.POST.get('start_date')
        workshop.end_date = request.POST.get('end_date')
        workshop.timings = request.POST.get('timings')
        workshop.description = request.POST.get('description')
        workshop.capacity = request.POST.get('capacity')
        if request.FILES.get('picture'):
            workshop.picture = request.FILES.get('picture')
        if request.FILES.get('poster'):
            workshop.poster = request.FILES.get('poster')
        workshop.save()
        messages.success(request, 'Workshop updated successfully!')
        return redirect('staff_workshops')
    return render(request, 'staff/staff_workshop_form.html', {
        'action': 'Edit',
        'workshop': workshop,
    })

@login_required
@staff_required
def staff_workshop_delete(request, workshop_id):
    if request.method == 'POST':
        workshop = get_object_or_404(Workshop, id=workshop_id)
        workshop.delete()
        messages.success(request, 'Workshop deleted successfully!')
    return redirect('staff_workshops')

@login_required
@staff_required
def staff_departments(request):
    departments = Department.objects.all().order_by('name')
    return render(request, 'staff/staff_departments.html', {
        'departments': departments,
    })

@login_required
@staff_required
def staff_department_add(request):
    if request.method == 'POST':
        Department.objects.create(
            name=request.POST.get('name'),
            location=request.POST.get('location'),
            area=request.POST.get('area'),
            supervisor=request.POST.get('supervisor'),
            timings=request.POST.get('timings'),
            eligibility=request.POST.get('eligibility'),
            has_evening_shift=request.POST.get('has_evening_shift') == 'on',
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Department added successfully!')
        return redirect('staff_departments')
    return render(request, 'staff/staff_department_form.html', {
        'action': 'Add',
        'department': None,
    })

@login_required
@staff_required
def staff_department_edit(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        department.name = request.POST.get('name')
        department.location = request.POST.get('location')
        department.area = request.POST.get('area')
        department.supervisor = request.POST.get('supervisor')
        department.timings = request.POST.get('timings')
        department.eligibility = request.POST.get('eligibility')
        department.has_evening_shift = request.POST.get('has_evening_shift') == 'on'
        department.is_active = request.POST.get('is_active') == 'on'
        department.save()
        messages.success(request, 'Department updated successfully!')
        return redirect('staff_departments')
    return render(request, 'staff/staff_department_form.html', {
        'action': 'Edit',
        'department': department,
    })

@login_required
@staff_required
def staff_department_delete(request, dept_id):
    if request.method == 'POST':
        department = get_object_or_404(Department, id=dept_id)
        department.delete()
        messages.success(request, 'Department deleted successfully!')
    return redirect('staff_departments')





@login_required
def workshops(request):
    workshops = Workshop.objects.filter(start_date__gte=date.today()).order_by('start_date')
    return render(request, 'workshops.html', {'workshops': workshops})

def logout_view(request):
    logout(request)
    return redirect('auth_page')