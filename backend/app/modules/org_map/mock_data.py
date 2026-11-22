"""Mock company structure in the shape of the shared contracts, until Supabase tables exist.

Employee ids, names, titles and teams match module 5's mock profiles
(backend/app/modules/onboarding/mock_data.py), and procedure ids match
data/company/procedures.json, so links between modules land on the same person and
procedure. Headcounts are the company's real sizes; only a few people per department are
listed.
"""

from .schemas import ContactResponsibility, Department, Employee

COMPANY_NAME = "نخلة للتقنية"

# The fake signed-in employee, until auth exists. Matches module 5's mock employee.
CURRENT_EMPLOYEE_ID = "emp-004"

# Mentors are assigned per new hire: employee id → mentor id.
MENTORS: dict[str, str] = {"emp-004": "emp-003", "emp-006": "emp-003", "emp-007": "emp-131"}

EXECUTIVE_ID = "dep-ceo"

DEPARTMENTS: list[Department] = [
    Department(
        id=EXECUTIVE_ID,
        name="الإدارة التنفيذية",
        head_id="emp-001",
        parent_id=None,
        teams=["الإدارة التنفيذية"],
    ),
    Department(
        id="dep-hr",
        name="الموارد البشرية",
        head_id="emp-101",
        parent_id=EXECUTIVE_ID,
        teams=["عمليات الموظفين", "التطوير والتدريب"],
    ),
    Department(
        id="dep-it",
        name="تقنية المعلومات",
        head_id="emp-005",
        parent_id=EXECUTIVE_ID,
        teams=["الدعم الفني", "الأمن السيبراني"],
    ),
    Department(
        id="dep-data",
        name="البيانات والتحليلات",
        head_id="emp-002",
        parent_id=EXECUTIVE_ID,
        teams=["البيانات والتحليلات", "هندسة البيانات", "الحوكمة"],
    ),
    Department(
        id="dep-finance",
        name="المالية",
        head_id="emp-111",
        parent_id=EXECUTIVE_ID,
        teams=["الحسابات", "المشتريات"],
    ),
    Department(
        id="dep-ops",
        name="العمليات",
        head_id="emp-121",
        parent_id=EXECUTIVE_ID,
        teams=["المرافق", "الأمن والسلامة"],
    ),
]

# Number of employees in each team, by department id.
TEAM_SIZES: dict[str, dict[str, int]] = {
    EXECUTIVE_ID: {"الإدارة التنفيذية": 1},
    "dep-hr": {"عمليات الموظفين": 9, "التطوير والتدريب": 5},
    "dep-it": {"الدعم الفني": 20, "الأمن السيبراني": 12},
    "dep-data": {"البيانات والتحليلات": 8, "هندسة البيانات": 7, "الحوكمة": 3},
    "dep-finance": {"الحسابات": 14, "المشتريات": 8},
    "dep-ops": {"المرافق": 90, "الأمن والسلامة": 38},
}


def _employee(
    id: str,
    full_name: str,
    gender: str,
    department_id: str,
    team: str,
    job_title: str,
    manager_id: str | None,
    email: str,
    office: str,
) -> Employee:
    return Employee(
        id=id,
        full_name=full_name,
        gender=gender,
        department_id=department_id,
        team=team,
        job_title=job_title,
        manager_id=manager_id,
        email=f"{email}@nakhla.example",
        office=office,
    )


EMPLOYEES: list[Employee] = [
    _employee(
        "emp-001",
        "خالد الدوسري",
        "m",
        EXECUTIVE_ID,
        "الإدارة التنفيذية",
        "الرئيس التنفيذي",
        None,
        "khalid.dosari",
        "الدور 8",
    ),
    _employee(
        "emp-002",
        "سارة القحطاني",
        "f",
        "dep-data",
        "البيانات والتحليلات",
        "مديرة البيانات",
        "emp-001",
        "sara.qahtani",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-003",
        "ريم الشهري",
        "f",
        "dep-data",
        "البيانات والتحليلات",
        "محللة بيانات أولى",
        "emp-002",
        "reem.shehri",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-141",
        "فهد العنزي",
        "m",
        "dep-data",
        "الحوكمة",
        "مسؤول حوكمة البيانات",
        "emp-002",
        "fahad.anazi",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-142",
        "عمر القرني",
        "m",
        "dep-data",
        "هندسة البيانات",
        "مهندس بيانات",
        "emp-002",
        "omar.qarni",
        "الدور 4 · جناح أ",
    ),
    _employee(
        "emp-006",
        "لمى السبيعي",
        "f",
        "dep-data",
        "البيانات والتحليلات",
        "محللة بيانات",
        "emp-002",
        "lama.subaie",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-004",
        "نورة العتيبي",
        "f",
        "dep-data",
        "البيانات والتحليلات",
        "محللة بيانات",
        "emp-002",
        "noura.otaibi",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-101",
        "مها العنزي",
        "f",
        "dep-hr",
        "عمليات الموظفين",
        "مديرة الموارد البشرية",
        "emp-001",
        "maha.anazi",
        "الدور 2",
    ),
    _employee(
        "emp-102",
        "منصور الشمري",
        "m",
        "dep-hr",
        "عمليات الموظفين",
        "أخصائي موارد بشرية",
        "emp-101",
        "mansour.shammari",
        "الدور 2",
    ),
    _employee(
        "emp-103",
        "هيا السالم",
        "f",
        "dep-hr",
        "التطوير والتدريب",
        "منسقة تدريب",
        "emp-101",
        "haya.salem",
        "الدور 2",
    ),
    _employee(
        "emp-005",
        "فهد المطيري",
        "m",
        "dep-it",
        "الدعم الفني",
        "مسؤول الصلاحيات",
        "emp-001",
        "fahad.mutairi",
        "الدور 3",
    ),
    _employee(
        "emp-007",
        "عبدالله الزهراني",
        "m",
        "dep-it",
        "الدعم الفني",
        "مطوّر برمجيات",
        "emp-005",
        "abdullah.zahrani",
        "الدور 3",
    ),
    _employee(
        "emp-131",
        "جود الرشيد",
        "f",
        "dep-it",
        "الأمن السيبراني",
        "محللة أمن سيبراني",
        "emp-005",
        "joud.rashid",
        "الدور 3",
    ),
    _employee(
        "emp-111",
        "منيرة الشهري",
        "f",
        "dep-finance",
        "الحسابات",
        "مديرة المالية",
        "emp-001",
        "munira.shehri",
        "الدور 5",
    ),
    _employee(
        "emp-112",
        "سلطان الحارثي",
        "m",
        "dep-finance",
        "الحسابات",
        "محاسب",
        "emp-111",
        "sultan.harthi",
        "الدور 5",
    ),
    _employee(
        "emp-113",
        "أمل الفيفي",
        "f",
        "dep-finance",
        "المشتريات",
        "أخصائية مشتريات",
        "emp-111",
        "amal.faifi",
        "الدور 5",
    ),
    _employee(
        "emp-121",
        "عبدالله المطيري",
        "m",
        "dep-ops",
        "المرافق",
        "مدير العمليات",
        "emp-001",
        "abdullah.mutairi",
        "الدور 1",
    ),
    _employee(
        "emp-122",
        "ناصر البقمي",
        "m",
        "dep-ops",
        "المرافق",
        "أخصائي مرافق",
        "emp-121",
        "nasser.baqami",
        "الدور 1",
    ),
    _employee(
        "emp-123",
        "ريما العسيري",
        "f",
        "dep-ops",
        "الأمن والسلامة",
        "مسؤولة سلامة",
        "emp-121",
        "reema.asiri",
        "الدور 1",
    ),
]

# Titles from data/company/procedures.json.
PROCEDURE_TITLES: dict[str, str] = {
    "proc-emergency-leave": "إجراء الإجازة الاضطرارية",
    "proc-employee-onboarding": "دليل الموظف الجديد",
    "proc-system-access": "إجراء طلب صلاحية نظام",
    "proc-phishing": "إجراء الإبلاغ عن التصيد",
    "proc-vpn": "دليل تفعيل الاتصال الآمن VPN",
    "proc-warehouse": "إجراء صلاحية مستودع البيانات",
    "proc-reimbursements": "إجراء تعويض مصاريف العمل",
    "proc-procurement": "إجراء طلب شراء أدوات",
    "proc-id-badge": "إجراء إصدار بطاقة دخول المبنى",
    "proc-incident": "إجراء الإبلاغ عن حادث سلامة",
    "proc-training-request": "إجراء طلب تدريب خارجي",
}


def _topic(employee_id: str, topic: str, procedure_id: str | None = None) -> ContactResponsibility:
    return ContactResponsibility(employee_id=employee_id, topic=topic, procedure_id=procedure_id)


# Approvers match module 5's access items: «مسؤول الصلاحيات» (emp-005) approves system
# access and VPN, and «مديرة البيانات» (emp-002) approves the data warehouse.
RESPONSIBILITIES: list[ContactResponsibility] = [
    _topic("emp-001", "استراتيجية الشركة"),
    _topic("emp-002", "اعتماد الإجازات"),
    _topic("emp-002", "موافقة صلاحية المستودع", "proc-warehouse"),
    _topic("emp-002", "تقييم الأداء"),
    _topic("emp-003", "لوحات المؤشرات"),
    _topic("emp-003", "Power BI"),
    _topic("emp-141", "حوكمة البيانات"),
    _topic("emp-141", "تصنيف البيانات"),
    _topic("emp-142", "مستودع البيانات"),
    _topic("emp-142", "خطوط معالجة البيانات"),
    _topic("emp-006", "تقارير المبيعات"),
    _topic("emp-101", "رصيد الإجازات"),
    _topic("emp-101", "الإجازة الاضطرارية", "proc-emergency-leave"),
    _topic("emp-102", "الموظفين الجدد", "proc-employee-onboarding"),
    _topic("emp-102", "الرواتب والبدلات"),
    _topic("emp-103", "التدريب والدورات", "proc-training-request"),
    _topic("emp-005", "صلاحيات الأنظمة", "proc-system-access"),
    _topic("emp-005", "الاتصال الآمن VPN", "proc-vpn"),
    _topic("emp-007", "الأنظمة الداخلية"),
    _topic("emp-131", "رسائل التصيد", "proc-phishing"),
    _topic("emp-131", "كلمات المرور والتحقق الثنائي"),
    _topic("emp-111", "اعتماد المصروفات", "proc-reimbursements"),
    _topic("emp-112", "تعويض المصاريف", "proc-reimbursements"),
    _topic("emp-112", "السفر لمهام العمل"),
    _topic("emp-113", "طلبات الشراء", "proc-procurement"),
    _topic("emp-121", "خدمات المكتب"),
    _topic("emp-122", "بطاقة دخول المبنى", "proc-id-badge"),
    _topic("emp-122", "حجز القاعات"),
    _topic("emp-123", "حوادث السلامة", "proc-incident"),
]
