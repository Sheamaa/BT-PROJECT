from django.core.mail import EmailMessage
from django.conf import settings
from .models import VolunteeringDocument

from django.core.mail import send_mail
from django.conf import settings

def send_application_submitted_email(user, department_name):
    send_mail(
        subject='Application Submitted — HPAP Volunteering',
        message=f'''
Dear {user.student_profile.full_name},

Your volunteering application to {department_name} has been successfully submitted.
Our team will review your application and notify you of the decision shortly.

Thank you for your interest in the HPAP Volunteering Program.

Best regards,
HPAP Team
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

def send_application_approved_email(user, department_name):
    send_mail(
        subject='Application Approved — HPAP Volunteering',
        message=f'''
Dear {user.student_profile.full_name},

Congratulations! Your volunteering application to {department_name} has been approved.
Please check your dashboard for further details and next steps.

We look forward to having you as part of our volunteering team.

Best regards,
HPAP Team
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

def send_application_rejected_email(user, department_name, reason):
    send_mail(
        subject='Application Update — HPAP Volunteering',
        message=f'''
Dear {user.student_profile.full_name},

We regret to inform you that your volunteering application to {department_name} has not been approved at this time.

Reason: {reason}

You are welcome to reapply after reviewing the feedback above.

Best regards,
HPAP Team
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

def send_workshop_registration_email(user, workshop_name):
    send_mail(
        subject='Workshop Registration Confirmed — HPAP',
        message=f'''
Dear {user.student_profile.full_name},

You have successfully registered for the workshop: {workshop_name}.
Please check your dashboard for further details.

Best regards,
HPAP Team
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

def send_application_approved_email(user, department):
    subject = 'Application Approved — HPAP Volunteering'
    body = f'''
Dear {user.student_profile.full_name},

Congratulations! Your volunteering application has been approved.

Activity Details:
- Department: {department.name}
- Location: {department.location}
- Supervisor: {department.supervisor}
- Timings: {department.timings}

Please find the attached volunteering documents. You will need to fill out the attendance sheet and upload it to the system after completing your volunteering activity.

We look forward to having you as part of our volunteering team.

Best regards,
HPAP Team
    '''
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    volunteering_docs = VolunteeringDocument.objects.all()
    for doc in volunteering_docs:
        try:
            doc.file.open()
            email.attach(doc.name, doc.file.read(), 'application/octet-stream')
            doc.file.close()
        except Exception:
            pass
    email.send(fail_silently=True)