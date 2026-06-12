# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from .models import (
    User, StudentProfile, StaffProfile, Department,
    DepartmentWeeklySlot, Application, Recommendation,
    Notification, Workshop, WorkshopRegistration
)
from .decision_tree import get_recommendation, build_tree, traverse_tree, DecisionNode, LeafNode
from django.core.files.uploadedfile import SimpleUploadedFile


# ══════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════

def create_student_user(username='student1', email='student1@test.com', password='testpass123'):
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='student'
    )

    dummy_pdf = SimpleUploadedFile(
        name="test.pdf",
        content=b"Dummy PDF content"
    )
    profile = StudentProfile.objects.create(
        user=user,
        full_name='Test Student',
        academic_level='undergraduate',
        grade_year='year-2',
        institution='Qatar University',
        phone='+974 5512 3456',
        qid='28734901234',
        qid_expiry_date=date.today() + timedelta(days=365),
        id_document=dummy_pdf
    )
    return user, profile


def create_staff_user(username='staff1', email='staff1@test.com', password='testpass123'):
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='staff'
    )
    StaffProfile.objects.create(
        user=user,
        full_name='Test Staff',
        access_level='coordinator'
    )
    return user


def create_department(name='Test Department', area='doha', eligibility='undergraduate', total_slots=5):
    return Department.objects.create(
        name=name,
        location='Doha',
        area=area,
        supervisor='Dr. Test',
        timings='Sun-Thu 8AM-2PM',
        eligibility=eligibility,
        total_slots=total_slots,
        is_active=True
    )


def create_weekly_slot(department, week_start=None, filled=0):
    if week_start is None:
        today = date.today()
        days = (6 - today.weekday()) % 7
        if days == 0:
            days = 7
        week_start = today + timedelta(days=days)
    return DepartmentWeeklySlot.objects.create(
        department=department,
        week_start_date=week_start,
        filled_slots=filled
    )


# ══════════════════════════════════════════
# MODEL TESTS
# ══════════════════════════════════════════

class UserModelTest(TestCase):

    def test_create_student_user(self):
        user, profile = create_student_user()
        self.assertEqual(user.role, 'student')
        self.assertEqual(user.email, 'student1@test.com')
        self.assertEqual(profile.full_name, 'Test Student')
        self.assertEqual(profile.user, user)

    def test_create_staff_user(self):
        user = create_staff_user()
        self.assertEqual(user.role, 'staff')
        self.assertTrue(hasattr(user, 'staff_profile'))

    def test_user_str(self):
        user, _ = create_student_user()
        self.assertIn('student1', str(user))
        self.assertIn('student', str(user))

    def test_student_profile_str(self):
        _, profile = create_student_user()
        self.assertEqual(str(profile), 'Test Student')


class DepartmentModelTest(TestCase):

    def test_create_department(self):
        dept = create_department()
        self.assertEqual(dept.name, 'Test Department')
        self.assertTrue(dept.is_active)
        self.assertEqual(dept.area, 'doha')

    def test_department_str(self):
        dept = create_department()
        self.assertEqual(str(dept), 'Test Department')


class DepartmentWeeklySlotTest(TestCase):

    def test_slot_not_full(self):
        dept = create_department(total_slots=5)
        slot = create_weekly_slot(dept, filled=3)
        self.assertFalse(slot.is_full())

    def test_slot_is_full(self):
        dept = create_department(total_slots=5)
        slot = create_weekly_slot(dept, filled=5)
        self.assertTrue(slot.is_full())

    def test_slot_str(self):
        dept = create_department()
        slot = create_weekly_slot(dept)
        self.assertIn('Test Department', str(slot))


class ApplicationModelTest(TestCase):

    def test_create_application(self):
        user, profile = create_student_user()
        dept = create_department()
        slot = create_weekly_slot(dept)
        app = Application.objects.create(
            student=profile,
            first_choice_dept=dept,
            preferred_slot=slot,
            status='submitted'
        )
        self.assertEqual(app.student, profile)
        self.assertEqual(app.status, 'submitted')
        self.assertEqual(app.first_choice_dept, dept)

    def test_application_str(self):
        user, profile = create_student_user()
        dept = create_department()
        slot = create_weekly_slot(dept)
        app = Application.objects.create(
            student=profile,
            first_choice_dept=dept,
            preferred_slot=slot,
            status='submitted'
        )
        self.assertIn('Test Student', str(app))
        self.assertIn('submitted', str(app))


class NotificationModelTest(TestCase):

    def test_create_notification(self):
        user, _ = create_student_user()
        notif = Notification.objects.create(
            user=user,
            message='Test notification',
            type='general',
            is_read=False
        )
        self.assertEqual(notif.user, user)
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.message, 'Test notification')


class WorkshopModelTest(TestCase):

    def test_create_workshop(self):
        workshop = Workshop.objects.create(
            name='First Aid Training',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            timings='9AM - 1PM',
            description='Learn first aid basics',
            capacity=30
        )
        self.assertEqual(workshop.name, 'First Aid Training')
        self.assertEqual(workshop.capacity, 30)

    def test_workshop_registration(self):
        user, profile = create_student_user()
        workshop = Workshop.objects.create(
            name='First Aid Training',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            timings='9AM - 1PM',
            description='Test',
            capacity=30
        )
        reg = WorkshopRegistration.objects.create(
            student=profile,
            workshop=workshop,
            status='registered'
        )
        self.assertEqual(reg.student, profile)
        self.assertEqual(reg.workshop, workshop)
        self.assertEqual(reg.status, 'registered')


# ══════════════════════════════════════════
# DECISION TREE TESTS
# ══════════════════════════════════════════

class DecisionTreeStructureTest(TestCase):

    def test_build_tree_returns_decision_node(self):
        root = build_tree()
        self.assertIsInstance(root, DecisionNode)

    def test_leaf_node_has_department_names(self):
        leaf = LeafNode(['Trauma and Emergency', 'TICU'])
        self.assertEqual(len(leaf.department_names), 2)
        self.assertIn('Trauma and Emergency', leaf.department_names)

    def test_decision_node_get_next(self):
        leaf_a = LeafNode(['Department A'])
        leaf_b = LeafNode(['Department B'])
        node = DecisionNode(
            question='Test question',
            attribute='test_attr',
            branches={'yes': leaf_a, 'no': leaf_b},
            default='no'
        )
        answers = {'test_attr': 'yes'}
        result = node.get_next(answers)
        self.assertEqual(result, leaf_a)

    def test_decision_node_default_branch(self):
        leaf_a = LeafNode(['Department A'])
        leaf_b = LeafNode(['Department B'])
        node = DecisionNode(
            question='Test question',
            attribute='test_attr',
            branches={'yes': leaf_a, 'no': leaf_b},
            default='no'
        )
        answers = {'test_attr': 'unknown_value'}
        result = node.get_next(answers)
        self.assertEqual(result, leaf_b)

    def test_traverse_tree_reaches_leaf(self):
        root = build_tree()
        answers = {
            'prior_experience': 'no',
            'willing_to_travel': 'yes',
            'stress_tolerance': 'high',
            'emergency_interest': 'yes',
            'preference': 'no_preference',
            'patient_interaction': 'very_comfortable',
            'work_type': 'no_preference',
        }
        leaf = traverse_tree(root, answers)
        self.assertIsInstance(leaf, LeafNode)
        self.assertTrue(len(leaf.department_names) > 0)


class DecisionTreeRecommendationTest(TestCase):

    def setUp(self):
        Department.objects.create(
            name='Outpatient Department',
            location='Doha', area='doha',
            supervisor='Dr. Test', timings='Sun-Thu',
            eligibility='highschool', is_active=True
        )
        Department.objects.create(
            name='Trauma and Emergency',
            location='Doha', area='doha',
            supervisor='Dr. Test', timings='Sun-Thu',
            eligibility='undergraduate', is_active=True
        )
        Department.objects.create(
            name='Mental Health',
            location='Doha', area='doha',
            supervisor='Dr. Test', timings='Sun-Thu',
            eligibility='undergraduate', is_active=True
        )
        Department.objects.create(
            name='Rumailah Hospital',
            location='Doha', area='doha',
            supervisor='Dr. Test', timings='Sun-Thu',
            eligibility='highschool', is_active=True
        )

    def test_no_experience_recommends_outpatient(self):
        answers = {
            'prior_experience': 'no',
            'willing_to_travel': 'yes',
            'stress_tolerance': 'low',
            'emergency_interest': 'no',
            'preference': 'no_preference',
            'patient_interaction': 'not_comfortable',
            'work_type': 'no_preference',
        }
        result = get_recommendation(answers, 'undergraduate', 'doha')
        self.assertIsNotNone(result)
        self.assertIn('Outpatient', result.name)

    def test_high_stress_emergency_recommends_trauma(self):
        answers = {
            'prior_experience': 'yes',
            'willing_to_travel': 'yes',
            'stress_tolerance': 'high',
            'emergency_interest': 'yes',
            'preference': 'no_preference',
            'patient_interaction': 'very_comfortable',
            'work_type': 'no_preference',
        }
        result = get_recommendation(answers, 'undergraduate', 'doha')
        self.assertIsNotNone(result)
        self.assertIn('Trauma', result.name)

    def test_area_filter_works(self):
        Department.objects.create(
            name='Al Khor Hospital',
            location='Al Khor', area='alkhor',
            supervisor='Dr. Test', timings='Sun-Thu',
            eligibility='highschool', is_active=True
        )
        answers = {
            'prior_experience': 'yes',
            'willing_to_travel': 'no',
            'stress_tolerance': 'low',
            'emergency_interest': 'no',
            'preference': 'elderly',
            'patient_interaction': 'somewhat',
            'work_type': 'no_preference',
        }
        result = get_recommendation(answers, 'undergraduate', 'alkhor')
        self.assertIsNotNone(result)
        self.assertEqual(result.area, 'alkhor')

    def test_highschool_cannot_get_undergraduate_dept(self):
        answers = {
            'prior_experience': 'yes',
            'willing_to_travel': 'yes',
            'stress_tolerance': 'high',
            'emergency_interest': 'yes',
            'preference': 'no_preference',
            'patient_interaction': 'very_comfortable',
            'work_type': 'no_preference',
        }
        result = get_recommendation(answers, 'high-school', 'doha')
        if result:
            self.assertEqual(result.eligibility, 'highschool')

    def test_recommendation_always_returns_result(self):
        answers = {
            'prior_experience': 'yes',
            'willing_to_travel': 'yes',
            'stress_tolerance': 'medium',
            'emergency_interest': 'not_sure',
            'preference': 'no_preference',
            'patient_interaction': 'somewhat',
            'work_type': 'no_preference',
        }
        result = get_recommendation(answers, 'undergraduate', 'doha')
        self.assertIsNotNone(result)


# ══════════════════════════════════════════
# VIEW TESTS
# ══════════════════════════════════════════

class PublicViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_landing_page_loads(self):
        response = self.client.get(reverse('landing_page'))
        self.assertEqual(response.status_code, 200)

    def test_auth_page_loads(self):
        response = self.client.get(reverse('auth_page'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_unauthenticated(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/', response.url)

    def test_profile_redirects_unauthenticated(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_apply_redirects_unauthenticated(self):
        response = self.client.get(reverse('apply'))
        self.assertEqual(response.status_code, 302)

    def test_staff_dashboard_redirects_unauthenticated(self):
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 302)


class StudentViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user, self.profile = create_student_user()
        self.client.login(username='student1', password='testpass123')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profile_loads(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_hospital_volunteering_loads(self):
        response = self.client.get(reverse('hospital_volunteering'))
        self.assertEqual(response.status_code, 200)

    def test_recommendation_page_loads(self):
        response = self.client.get(reverse('recommendation'))
        self.assertEqual(response.status_code, 200)

    def test_apply_page_loads(self):
        response = self.client.get(reverse('apply'))
        self.assertEqual(response.status_code, 200)

    def test_workshops_page_loads(self):
        response = self.client.get(reverse('workshops'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_staff_dashboard(self):
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_profile_update(self):
        response = self.client.post(reverse('profile'), {
            'full_name': 'Updated Name',
            'phone': '+974 5512 9999',
            'qid': '28734901234',
            'academic_level': 'undergraduate',
            'grade_year': 'year-2',
            'institution': 'Qatar University',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Updated Name')

    def test_dashboard_shows_applications(self):
        dept = create_department()
        slot = create_weekly_slot(dept)
        Application.objects.create(
            student=self.profile,
            first_choice_dept=dept,
            preferred_slot=slot,
            status='submitted'
        )
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('applications', response.context)
        self.assertEqual(response.context['applications'].count(), 1)


class StaffViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff_user = create_staff_user()
        self.client.login(username='staff1', password='testpass123')

    def test_staff_dashboard_loads(self):
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_staff_departments_loads(self):
        response = self.client.get(reverse('staff_departments'))
        self.assertEqual(response.status_code, 200)

    def test_staff_workshops_loads(self):
        response = self.client.get(reverse('staff_workshops'))
        self.assertEqual(response.status_code, 200)

    def test_staff_students_loads(self):
        response = self.client.get(reverse('staff_students'))
        self.assertEqual(response.status_code, 200)

    def test_staff_attendance_loads(self):
        response = self.client.get(reverse('staff_attendance_list'))
        self.assertEqual(response.status_code, 200)

    def test_staff_certificates_loads(self):
        response = self.client.get(reverse('staff_certificates_list'))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_add_department(self):
        response = self.client.post(reverse('staff_department_add'), {
            'name': 'New Department',
            'location': 'Doha',
            'area': 'doha',
            'supervisor': 'Dr. New',
            'timings': 'Sun-Thu 8AM-2PM',
            'eligibility': 'undergraduate',
            'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(name='New Department').exists())

    def test_staff_can_approve_application(self):
        student_user, student_profile = create_student_user(
            username='student2', email='student2@test.com'
        )
        dept = create_department()
        slot = create_weekly_slot(dept)
        app = Application.objects.create(
            student=student_profile,
            first_choice_dept=dept,
            preferred_slot=slot,
            status='submitted'
        )
        response = self.client.post(
            reverse('approve_application', args=[app.id]),
            {'choice': 'first'}
        )
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, 'approved')

    def test_staff_can_reject_application(self):
        student_user, student_profile = create_student_user(
            username='student3', email='student3@test.com'
        )
        dept = create_department()
        slot = create_weekly_slot(dept)
        app = Application.objects.create(
            student=student_profile,
            first_choice_dept=dept,
            preferred_slot=slot,
            status='submitted'
        )
        response = self.client.post(
            reverse('reject_application', args=[app.id]),
            {'reason': 'Does not meet requirements'}
        )
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, 'rejected')

    def test_approve_full_slot_fails(self):
        student_user, student_profile = create_student_user(
            username='student4', email='student4@test.com'
        )
        dept = create_department(total_slots=5)
        slot = create_weekly_slot(dept, filled=5)
        app = Application.objects.create(
            student=student_profile,
            first_choice_dept=dept,
            preferred_slot=slot,
            status='submitted'
        )
        response = self.client.post(
            reverse('approve_application', args=[app.id]),
            {'choice': 'first'}
        )
        app.refresh_from_db()
        self.assertNotEqual(app.status, 'approved')


# ══════════════════════════════════════════
# APPLICATION LOGIC TESTS
# ══════════════════════════════════════════

class ApplicationLogicTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user, self.profile = create_student_user()
        self.client.login(username='student1', password='testpass123')
        self.dept = create_department()
        self.slot = create_weekly_slot(self.dept)

    def test_student_cannot_submit_two_active_applications(self):
        Application.objects.create(
            student=self.profile,
            first_choice_dept=self.dept,
            preferred_slot=self.slot,
            status='submitted'
        )
        next_sunday = date.today() + timedelta(days=(6 - date.today().weekday() + 7) % 7 + 1)
        slot2 = DepartmentWeeklySlot.objects.create(
            department=self.dept,
            week_start_date=next_sunday,
            filled_slots=0
        )
        response = self.client.post(reverse('apply'), {
            'first_choice_dept': self.dept.id,
            'preferred_week': str(next_sunday),
        })
        self.assertEqual(
            Application.objects.filter(student=self.profile).count(), 1
        )

    def test_slot_filled_after_approval(self):
        student_user2 = create_staff_user(
            username='staff2', email='staff2@test.com'
        )
        self.client.logout()
        self.client.login(username='staff2', password='testpass123')

        student_user, student_profile = create_student_user(
            username='student5', email='student5@test.com'
        )
        app = Application.objects.create(
            student=student_profile,
            first_choice_dept=self.dept,
            preferred_slot=self.slot,
            status='submitted'
        )
        initial_filled = self.slot.filled_slots
        self.client.post(
            reverse('approve_application', args=[app.id]),
            {'choice': 'first'}
        )
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.filled_slots, initial_filled + 1)


# ══════════════════════════════════════════
# WORKSHOP TESTS
# ══════════════════════════════════════════

class WorkshopTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user, self.profile = create_student_user()
        self.client.login(username='student1', password='testpass123')
        self.workshop = Workshop.objects.create(
            name='Test Workshop',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=8),
            timings='9AM-1PM',
            description='Test',
            capacity=10
        )

    def test_student_can_register_for_workshop(self):
        response = self.client.post(
            reverse('register_workshop', args=[self.workshop.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            WorkshopRegistration.objects.filter(
                student=self.profile,
                workshop=self.workshop
            ).exists()
        )

    def test_capacity_decreases_after_registration(self):
        initial_capacity = self.workshop.capacity
        self.client.post(
            reverse('register_workshop', args=[self.workshop.id])
        )
        self.workshop.refresh_from_db()
        self.assertEqual(self.workshop.capacity, initial_capacity - 1)

    def test_student_cannot_register_twice(self):
        self.client.post(reverse('register_workshop', args=[self.workshop.id]))
        self.client.post(reverse('register_workshop', args=[self.workshop.id]))
        self.assertEqual(
            WorkshopRegistration.objects.filter(
                student=self.profile,
                workshop=self.workshop
            ).count(), 1
        )


# ══════════════════════════════════════════
# NOTIFICATION TESTS
# ══════════════════════════════════════════

class NotificationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user, self.profile = create_student_user()
        self.client.login(username='student1', password='testpass123')

    

    def test_notification_created_on_application_submit(self):
        dept = create_department()

        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)

        slot = DepartmentWeeklySlot.objects.create(
            department=dept,
            week_start_date=next_sunday,
            filled_slots=0
        )


        response = self.client.post(reverse('apply'), {
            'first_choice_dept': str(dept.id),
            'preferred_week': str(next_sunday),
        })


        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                type='application_submitted',
                is_read=False
            ).exists()
        )


    def test_mark_all_notifications_read(self):
        Notification.objects.create(
            user=self.user,
            message='Test 1',
            type='general',
            is_read=False
        )

        Notification.objects.create(
            user=self.user,
            message='Test 2',
            type='general',
            is_read=False
        )
        self.client.get(reverse('mark_all_read'))
        unread = Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
        self.assertEqual(unread, 0)