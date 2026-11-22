"""Mock data in the exact shape of the shared contracts.

Used until Supabase tables and auth exist. Department ids must match the
mock data of module 4 (org-map); procedure ids match data/company/procedures.json.
"""

from .schemas import (
    AccessItem,
    AccessStatus,
    EmployeeAccess,
    EmployeeProfile,
)

# The fake signed-in employee (a new hire).
CURRENT_EMPLOYEE_ID = "emp-004"

# Employees the demo can switch between: three new hires with different paths, and a manager.
DEMO_EMPLOYEE_IDS = ["emp-004", "emp-006", "emp-007", "emp-002"]

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
    EmployeeProfile(
        id="emp-006",
        full_name="لمى السبيعي",
        department_id="dep-data",
        team="البيانات والتحليلات",
        job_title="محللة بيانات",
        manager_id="emp-002",
        years_of_experience=2,
        role="employee",
    ),
    EmployeeProfile(
        id="emp-007",
        full_name="عبدالله الزهراني",
        department_id="dep-it",
        team="الدعم الفني",
        job_title="مطوّر برمجيات",
        manager_id="emp-005",
        years_of_experience=0,
        role="employee",
    ),
]

ACCESS_ITEMS: list[AccessItem] = [
    AccessItem(
        id="acc-email",
        system_name="البريد الإلكتروني",
        required_for_job_titles=[
            "محللة بيانات",
            "محللة بيانات أولى",
            "مديرة البيانات",
            "مطوّر برمجيات",
        ],
        procedure_id="proc-system-access",
        approver_role="مسؤول الصلاحيات",
        expected_days=1,
    ),
    AccessItem(
        id="acc-hr",
        system_name="نظام الموارد البشرية",
        required_for_job_titles=[
            "محللة بيانات",
            "محللة بيانات أولى",
            "مديرة البيانات",
            "مطوّر برمجيات",
        ],
        procedure_id="proc-system-access",
        approver_role="المدير المباشر",
        expected_days=2,
    ),
    AccessItem(
        id="acc-vpn",
        system_name="الشبكة الخاصة (VPN)",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى", "مطوّر برمجيات"],
        procedure_id="proc-vpn",
        approver_role="مسؤول الصلاحيات",
        expected_days=3,
    ),
    AccessItem(
        id="acc-dwh",
        system_name="مستودع البيانات",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى"],
        procedure_id="proc-warehouse",
        approver_role="مديرة البيانات",
        expected_days=5,
    ),
    AccessItem(
        id="acc-bi",
        system_name="Power BI",
        required_for_job_titles=["محللة بيانات", "محللة بيانات أولى"],
        procedure_id="proc-procurement",
        approver_role="المدير المباشر",
        expected_days=3,
    ),
    AccessItem(
        id="acc-git",
        system_name="مستودع الشيفرة (GitHub)",
        required_for_job_titles=["مطوّر برمجيات"],
        procedure_id="proc-system-access",
        approver_role="مسؤول الصلاحيات",
        expected_days=2,
    ),
    AccessItem(
        id="acc-staging",
        system_name="بيئة الاختبار",
        required_for_job_titles=["مطوّر برمجيات"],
        procedure_id="proc-system-access",
        approver_role="المدير المباشر",
        expected_days=4,
    ),
]


def _access(employee_id: str, statuses: dict[str, AccessStatus]) -> list[EmployeeAccess]:
    return [
        EmployeeAccess(employee_id=employee_id, access_item_id=item_id, status=status)
        for item_id, status in statuses.items()
    ]


EMPLOYEE_ACCESS: list[EmployeeAccess] = [
    # Sara (manager) and Reem (senior analyst): everything active.
    *_access("emp-002", {"acc-email": "active", "acc-hr": "active"}),
    *_access(
        "emp-003",
        {
            "acc-email": "active",
            "acc-hr": "active",
            "acc-vpn": "active",
            "acc-dwh": "active",
            "acc-bi": "active",
        },
    ),
    # Noura: half way.
    *_access(
        "emp-004",
        {
            "acc-email": "active",
            "acc-hr": "active",
            "acc-vpn": "requested",
            "acc-dwh": "missing",
            "acc-bi": "missing",
        },
    ),
    # Lama: almost done.
    *_access(
        "emp-006",
        {
            "acc-email": "active",
            "acc-hr": "active",
            "acc-vpn": "active",
            "acc-dwh": "active",
            "acc-bi": "requested",
        },
    ),
    # Abdullah: first day, only email.
    *_access(
        "emp-007",
        {
            "acc-email": "active",
            "acc-hr": "requested",
            "acc-vpn": "missing",
            "acc-git": "missing",
            "acc-staging": "missing",
        },
    ),
]
