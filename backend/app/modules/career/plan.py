"""A simple 30/60/90-day development plan built from the gap analysis.

Rule-based on purpose: every action names a skill the target title's postings ask for, and
its reason is the market share already shown in the gap, so the plan invents nothing.
Skills the employee lacks come first, the most requested first, then skills to improve.
"""

from .repository import CareerRepository
from .schemas import ActionType, DevelopmentPlan, GapAnalysis, GapSkill, PlanAction, PlanPhase

SKILLS_PER_PHASE = 2
HOURS_TO_LEARN = 20
HOURS_TO_IMPROVE = 10

# How each kind of skill is usually built: (first action, second action).
ACTIONS_BY_CATEGORY: dict[str, tuple[ActionType, ActionType]] = {
    "technical": ("course", "project"),
    "tool": ("course", "project"),
    "soft": ("mentoring", "shadowing"),
    "domain": ("reading", "shadowing"),
    "language": ("course", "project"),
}
# Skills that are themselves a credential.
CERTIFICATION_SKILLS = {"cpa_cma"}

TITLES: dict[ActionType, str] = {
    "course": "دورة تدريبية في «{skill}»",
    "project": "تطبيق «{skill}» في مهمة حقيقية في فريقك",
    "mentoring": "جلسات توجيه مع مديرك أو زميل خبير في «{skill}»",
    "shadowing": "مرافقة شخص بمنصب «{target}» وهو يمارس «{skill}»",
    "reading": "قراءة سياسات الشركة ومراجعها عن «{skill}»",
    "certification": "شهادة مهنية في «{skill}»",
}

METRICS: dict[ActionType, str] = {
    "course": "إنهاء الدورة وتطبيق تمرين واحد على الأقل",
    "project": "مهمة مسلّمة يراجعها مديرك",
    "mentoring": "٣ جلسات موثّقة بملاحظات",
    "shadowing": "ملخص مكتوب لما تعلّمته من موقفين",
    "reading": "ملخص صفحة واحدة تراجعه مع مديرك",
    "certification": "اجتياز الاختبار",
}

GOALS = {
    "30": "بناء الأساس في {skills}",
    "60": "التطوير في {skills}",
    "90": "إثبات الجاهزية لمنصب «{target}» في {skills}",
}


def _ordered(gap: GapAnalysis) -> list[tuple[GapSkill, bool]]:
    """Skills to work on, most urgent first. The flag says whether the skill is new."""
    missing = sorted(gap.gap.missing, key=lambda s: -s.market_frequency)
    improve = sorted(
        gap.gap.to_improve,
        key=lambda s: -(s.market_frequency * (s.expected_level - s.employee_level)),
    )
    return [(s, True) for s in missing] + [(s, False) for s in improve]


def _actions(skill: GapSkill, is_new: bool, skill_row: dict, target: str) -> list[PlanAction]:
    hours = HOURS_TO_LEARN if is_new else HOURS_TO_IMPROVE
    if skill_row["key"] in CERTIFICATION_SKILLS:
        types: list[ActionType] = ["certification"]
    else:
        first, second = ACTIONS_BY_CATEGORY.get(skill_row["category"], ("reading", "project"))
        # A skill the employee already has needs practice, not another introduction.
        types = [first, second] if is_new else [second]
    return [
        PlanAction(
            skill_id=skill.skill_id,
            type=t,
            title_ar=TITLES[t].format(skill=skill.label_ar, target=target),
            effort_hours=hours // len(types),
            success_metric_ar=METRICS[t],
        )
        for t in types
    ]


def build_plan(repo: CareerRepository, gap: GapAnalysis) -> DevelopmentPlan:
    target = repo.titles[gap.target_title_id]["name_ar"]
    skills = _ordered(gap)
    phases = []
    for index, phase in enumerate(("30", "60", "90")):
        chunk = skills[index * SKILLS_PER_PHASE : (index + 1) * SKILLS_PER_PHASE]
        if not chunk:
            continue
        names = " و".join(f"«{s.label_ar}»" for s, _ in chunk)
        phases.append(
            PlanPhase(
                phase=phase,
                goal_ar=GOALS[phase].format(skills=names, target=target),
                actions=[
                    action
                    for s, is_new in chunk
                    for action in _actions(s, is_new, repo.skills[s.skill_id], target)
                ],
            )
        )
    return DevelopmentPlan(
        current_title_id=gap.current_title_id,
        target_title_id=gap.target_title_id,
        readiness_score=gap.readiness_score,
        low_evidence=gap.gap.low_evidence,
        phases=phases,
    )
