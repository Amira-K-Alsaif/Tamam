"""Mock data in the exact shape of the shared contracts.

Used until Supabase tables and auth exist. Department ids must match the
mock data of module 4 (org-map).
"""

from datetime import UTC, datetime

from .schemas import AccessItem, AssessmentResult, EmployeeAccess, EmployeeProfile

# The fake signed-in employee (a new hire).
CURRENT_EMPLOYEE_ID = "emp-004"

# When the mock starting assessment was taken (6am UTC = 9am Riyadh).
ASSESSMENT_TAKEN_AT = datetime(2026, 11, 2, 6, 0, tzinfo=UTC)

EMPLOYEES: list[EmployeeProfile] = [
    EmployeeProfile(
        id="emp-001",
        full_name="خالد الدوسري",
        department_id="dep-ceo",
        team="الإدارة التنفيذية",
        job_title="الرئيس التنفيذي",
        manager_id=None,
        years_of_experience=20,
        role="admin",
    ),
    EmployeeProfile(
        id="emp-002",
        full_name="سارة القحطاني",
        department_id="dep-data",
        team="البيانات والتحليلات",
        job_title="مديرة البيانات",
        manager_id="emp-001",
        years_of_experience=12,
        role="employee",
    ),
    EmployeeProfile(
        id="emp-003",
        full_name="ريم الشهري",
        department_id="dep-data",
        team="البيانات والتحليلات",
        job_title="محللة بيانات أولى",
        manager_id="emp-002",
        years_of_experience=6,
        role="employee",
    ),
    EmployeeProfile(
        id="emp-004",
        full_name="نورة العتيبي",
        department_id="dep-data",
        team="البيانات والتحليلات",
        job_title="محللة بيانات",
        manager_id="emp-002",
        years_of_experience=0,
        role="employee",
    ),
    EmployeeProfile(
        id="emp-005",
        full_name="فهد المطيري",
        department_id="dep-it",
        team="الدعم الفني",
        job_title="مسؤول الصلاحيات",
        manager_id="emp-001",
        years_of_experience=8,
        role="admin",
    ),
]

ACCESS_ITEMS: list[AccessItem] = [
    AccessItem(
        id="acc-email",
        system_name="البريد الإلكتروني",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى", "مديرة البيانات"],
        procedure_id="proc-it-account",
        approver_role="مسؤول الصلاحيات",
        expected_days=1,
    ),
    AccessItem(
        id="acc-hr",
        system_name="نظام الموارد البشرية",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى", "مديرة البيانات"],
        procedure_id="proc-hr-access",
        approver_role="المدير المباشر",
        expected_days=2,
    ),
    AccessItem(
        id="acc-vpn",
        system_name="الشبكة الخاصة (VPN)",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى"],
        procedure_id="proc-vpn",
        approver_role="مسؤول الصلاحيات",
        expected_days=3,
    ),
    AccessItem(
        id="acc-dwh",
        system_name="مستودع البيانات",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى"],
        procedure_id="proc-data-access",
        approver_role="مديرة البيانات",
        expected_days=5,
    ),
    AccessItem(
        id="acc-bi",
        system_name="Power BI",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى"],
        procedure_id="proc-software-license",
        approver_role="المدير المباشر",
        expected_days=3,
    ),
]

EMPLOYEE_ACCESS: list[EmployeeAccess] = [
    EmployeeAccess(employee_id="emp-004", access_item_id="acc-email", status="active"),
    EmployeeAccess(employee_id="emp-004", access_item_id="acc-hr", status="active"),
    EmployeeAccess(employee_id="emp-004", access_item_id="acc-vpn", status="requested"),
    EmployeeAccess(employee_id="emp-004", access_item_id="acc-dwh", status="missing"),
    EmployeeAccess(employee_id="emp-004", access_item_id="acc-bi", status="missing"),
]

ASSESSMENT_RESULTS: list[AssessmentResult] = [
    AssessmentResult(
        employee_id="emp-004", topic="سياسة الإجازات", score=80, taken_at=ASSESSMENT_TAKEN_AT
    ),
    AssessmentResult(
        employee_id="emp-004", topic="الحضور والانصراف", score=65, taken_at=ASSESSMENT_TAKEN_AT
    ),
    AssessmentResult(
        employee_id="emp-004", topic="أمن المعلومات", score=40, taken_at=ASSESSMENT_TAKEN_AT
    ),
    AssessmentResult(
        employee_id="emp-004", topic="السفر والانتداب", score=30, taken_at=ASSESSMENT_TAKEN_AT
    ),
    AssessmentResult(
        employee_id="emp-004", topic="المصروفات والمطالبات", score=55, taken_at=ASSESSMENT_TAKEN_AT
    ),
]
