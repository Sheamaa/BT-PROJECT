from .models import Department

def get_recommendation(answers, academic_level, student_area):

    willing_to_travel = answers.get('willing_to_travel')
    prior_experience = answers.get('prior_experience')
    stress_tolerance = answers.get('stress_tolerance')
    patient_interaction = answers.get('patient_interaction')
    preference = answers.get('preference')
    emergency_interest = answers.get('emergency_interest')
    work_type = answers.get('work_type')

    # Step 1 — determine available areas
    if willing_to_travel == 'yes':
        available_areas = ['doha', 'alwakra', 'alkhor', 'dukhan']
    else:
        available_areas = [student_area]

    # Step 2 — determine eligibility based on academic level
    if academic_level in ['high-school']:
        eligible = ['highschool']
    else:
        eligible = ['highschool', 'undergraduate']

    # Step 3 — get all available departments for this student
    available_depts = Department.objects.filter(
        area__in=available_areas,
        eligibility__in=eligible,
        is_active=True
    )

    # Step 4 — no prior experience → always recommend Outpatient Department first
    if prior_experience == 'no':
        dept = available_depts.filter(
            name__icontains='Outpatient'
        ).first()
        if dept:
            return dept
        # if outpatient not in their area fallback to ambulatory
        dept = available_depts.filter(
            name__icontains='Ambulatory'
        ).first()
        if dept:
            return dept

    # Step 5 — decision tree for experienced students
    # HIGH stress tolerance path
    if stress_tolerance == 'high':
        if emergency_interest == 'yes':
            if preference == 'children':
                target_names = [
                    'Pediatric Emergency Al Sadd',
                    'Pediatric Emergency Al Rayyan',
                ]
            else:
                target_names = ['Trauma and Emergency', 'TICU', 'MICU']

        elif emergency_interest == 'not_sure':
            if work_type == 'technical':
                target_names = ['QRI', 'Environmental Safety']
            else:
                target_names = ['Internal Medicine', 'MICU', 'Heart Hospital']

        else:
            if work_type == 'technical':
                target_names = ['QRI', 'Environmental Safety']
            elif preference == 'children':
                target_names = [
                    'Child Development',
                    'Pediatric Emergency Al Sadd',
                    'Pediatric Emergency Al Rayyan',
                ]
            else:
                target_names = ['Internal Medicine', 'Heart Hospital']

    # MEDIUM stress tolerance path
    elif stress_tolerance == 'medium':
        if preference == 'children':
            target_names = [
                'Child Development',
                'Pediatric Emergency Al Sadd',
                'Pediatric Emergency Al Rayyan',
            ]
        elif preference == 'elderly':
            target_names = ['Rumailah Hospital', 'Al Khor Hospital',
                           'Al Wakra Hospital']
        elif work_type == 'technical':
            target_names = ['QRI', 'Environmental Safety']
        elif emergency_interest == 'yes':
            target_names = ['Trauma and Emergency', 'Heart Hospital']
        else:
            target_names = ['Mental Health', 'Internal Medicine',
                           'Heart Hospital']

    # LOW stress tolerance path
    else:
        if preference == 'elderly':
            target_names = ['Rumailah Hospital', 'Al Khor Hospital',
                           'Al Wakra Hospital', 'Aisha Hospital']
        elif preference == 'children':
            target_names = [
                'Child Development',
                'Pediatric Emergency Al Sadd',
                'Pediatric Emergency Al Rayyan',
            ]
        elif patient_interaction == 'not_comfortable':
            target_names = [
                'Ambulatory Care Center',
                'Outpatient Department',
                'Environmental Safety',
            ]
        elif work_type == 'administrative':
            target_names = [
                'Outpatient Department',
                'Ambulatory Care Center',
            ]
        else:
            target_names = [
                'Mental Health',
                'Al Wakra Hospital',
                'Al Khor Hospital',
                'Cuban Hospital',
                'Aisha Hospital',
            ]

    # Step 6 — find best match from available departments
    for name in target_names:
        dept = available_depts.filter(name__icontains=name).first()
        if dept:
            return dept

    # Step 7 — fallback if nothing matched
    return available_depts.first()