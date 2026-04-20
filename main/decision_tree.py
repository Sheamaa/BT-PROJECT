from .models import Department


class DecisionNode:
    def __init__(self, question, attribute, branches, default=None):
        self.question = question
        self.attribute = attribute
        self.branches = branches
        self.default = default

    def get_next(self, answers):
        value = answers.get(self.attribute, self.default)
        if value in self.branches:
            return self.branches[value]
        if self.default and self.default in self.branches:
            return self.branches[self.default]
        return list(self.branches.values())[0]


class LeafNode:
    def __init__(self, department_names):
        self.department_names = department_names


def build_tree():
    # ── LEAF NODES ──────────────────────────────────────────────
    # Each leaf represents the end of a path through the tree
    # department_names is ordered by preference — we pick the
    # first one that exists in the student's available pool

    leaf_trauma = LeafNode([
        'Trauma and Emergency',
        'TICU',
        'MICU',
    ])

    leaf_pediatric_emergency = LeafNode([
        'Pediatric Emergency Al Sadd',
        'Pediatric Emergency Al Rayyan',
        'Child Development',
    ])

    leaf_technical = LeafNode([
        'QRI',
        'Environmental Safety',
        'Internal Medicine',
    ])

    leaf_icu = LeafNode([
        'MICU',
        'TICU',
        'Internal Medicine',
    ])

    leaf_children = LeafNode([
        'Child Development',
        'Pediatric Emergency Al Sadd',
        'Pediatric Emergency Al Rayyan',
    ])

    leaf_elderly = LeafNode([
        'Rumailah Hospital',
        'Al Khor Hospital',
        'Al Wakra Hospital',
        'Aisha Hospital',
    ])

    leaf_admin = LeafNode([
        'Outpatient Department',
        'Ambulatory Care Center',
        'Environmental Safety',
    ])

    leaf_mental_health = LeafNode([
        'Mental Health',
        'Heart Hospital',
        'Al Wakra Hospital',
    ])

    leaf_general = LeafNode([
        'Heart Hospital',
        'Al Wakra Hospital',
        'Al Khor Hospital',
        'Cuban Hospital',
        'Aisha Hospital',
    ])

    leaf_outpatient = LeafNode([
        'Outpatient Department',
        'Ambulatory Care Center',
    ])

    # ── LEVEL 3 NODES (deepest questions) ───────────────────────
    # These nodes are reached after answering stress and emergency

    # High stress + emergency yes → do they prefer children?
    node_emergency_preference = DecisionNode(
        question='Do you prefer working with children?',
        attribute='preference',
        branches={
            'children': leaf_pediatric_emergency,
            'elderly':  leaf_trauma,
            'no_preference': leaf_trauma,
        },
        default='no_preference'
    )

    # High stress + emergency not sure → technical interest?
    node_high_not_sure = DecisionNode(
        question='Are you interested in technical work?',
        attribute='work_type',
        branches={
            'technical':      leaf_technical,
            'administrative': leaf_icu,
            'no_preference':  leaf_icu,
        },
        default='no_preference'
    )

    # High stress + emergency no → technical or other?
    node_high_no_emergency = DecisionNode(
        question='What type of work interests you?',
        attribute='work_type',
        branches={
            'technical':      leaf_technical,
            'administrative': leaf_icu,
            'no_preference':  leaf_icu,
        },
        default='no_preference'
    )

    # Medium stress → patient preference
    node_medium_preference = DecisionNode(
        question='Do you prefer working with children or elderly?',
        attribute='preference',
        branches={
            'children':     leaf_children,
            'elderly':      leaf_elderly,
            'no_preference': leaf_mental_health,
        },
        default='no_preference'
    )

    # Low stress + comfortable with patients → preference
    node_low_comfortable = DecisionNode(
        question='Do you prefer working with children or elderly?',
        attribute='preference',
        branches={
            'children':     leaf_children,
            'elderly':      leaf_elderly,
            'no_preference': leaf_mental_health,
        },
        default='no_preference'
    )

    # Low stress + not comfortable → work type
    node_low_not_comfortable = DecisionNode(
        question='What type of work interests you?',
        attribute='work_type',
        branches={
            'technical':      leaf_technical,
            'administrative': leaf_admin,
            'no_preference':  leaf_admin,
        },
        default='no_preference'
    )

    # ── LEVEL 2 NODES ───────────────────────────────────────────

    # High stress → emergency interest?
    node_high_stress = DecisionNode(
        question='Are you interested in emergency care?',
        attribute='emergency_interest',
        branches={
            'yes':      node_emergency_preference,
            'not_sure': node_high_not_sure,
            'no':       node_high_no_emergency,
        },
        default='not_sure'
    )

    # Medium stress → preference
    node_medium_stress = node_medium_preference

    # Low stress → patient interaction comfort?
    node_low_stress = DecisionNode(
        question='Are you comfortable with direct patient interaction?',
        attribute='patient_interaction',
        branches={
            'very_comfortable': node_low_comfortable,
            'somewhat':         node_low_comfortable,
            'not_comfortable':  node_low_not_comfortable,
        },
        default='somewhat'
    )

    # ── LEVEL 1 NODE ────────────────────────────────────────────

    # Prior experience check → if no experience go straight to outpatient
    node_experience = DecisionNode(
        question='Do you have prior volunteering experience?',
        attribute='prior_experience',
        branches={
            'yes': DecisionNode(
                question='How do you handle stress?',
                attribute='stress_tolerance',
                branches={
                    'high':   node_high_stress,
                    'medium': node_medium_stress,
                    'low':    node_low_stress,
                },
                default='medium'
            ),
            'no': leaf_outpatient,
        },
        default='yes'
    )

    # ── ROOT NODE ────────────────────────────────────────────────
    # The very first question asked
    root = node_experience

    return root


def traverse_tree(node, answers):
    # This function walks the tree from root to leaf
    # It keeps moving as long as the current node is a DecisionNode
    # When it reaches a LeafNode it stops and returns it

    while isinstance(node, DecisionNode):
        # get_next looks at the student's answer for this node's
        # attribute and returns the matching child node
        node = node.get_next(answers)

    # at this point node is a LeafNode
    return node


def get_recommendation(answers, academic_level, student_area):
    # Step 1 — determine which areas are available
    willing_to_travel = answers.get('willing_to_travel')
    if willing_to_travel == 'yes':
        available_areas = ['doha', 'alwakra', 'alkhor', 'dukhan']
    else:
        available_areas = [student_area]

    # Step 2 — determine eligibility based on academic level
    if academic_level == 'high-school':
        eligible = ['highschool']
    else:
        eligible = ['highschool', 'undergraduate']

    # Step 3 — get all departments this student can apply to
    available_depts = Department.objects.filter(
        area__in=available_areas,
        eligibility__in=eligible,
        is_active=True
    )

    # Step 4 — build the tree
    root = build_tree()

    # Step 5 — traverse the tree with the student's answers
    # this returns a LeafNode containing a list of department names
    leaf = traverse_tree(root, answers)

    # Step 6 — find the best matching department from the leaf's list
    # we go through the leaf's department_names in order and return
    # the first one that exists in the student's available pool
    for dept_name in leaf.department_names:
        dept = available_depts.filter(
            name__icontains=dept_name
        ).first()
        if dept:
            return dept

    # Step 7 — fallback: if nothing matched return any available dept
    return available_depts.first()