"""Mock company structure in the shape of the shared contracts, until Supabase tables exist.

Names, departments and teams follow data/company/company_profile.json (fictional company).
Headcounts are the company's real sizes; only a few people per department are listed.
"""

from .schemas import ContactResponsibility, Department, Employee

COMPANY_NAME = "نخلة للتقنية"

# The fake signed-in employee, until auth exists. Matches module 5's mock employee.
CURRENT_EMPLOYEE_ID = "emp-004"

# Mentors are assigned per new hire: employee id → mentor id.
MENTORS: dict[str, str] = {"emp-004": "emp-203"}

EXECUTIVE_ID = "executive"

DEPARTMENTS: list[Department] = [
    Department(
        id=EXECUTIVE_ID,
        name="الإدارة التنفيذية",
        head_id="emp-101",
        parent_id=None,
        teams=["الإدارة التنفيذية"],
    ),
    Department(
        id="hr",
        name="الموارد البشرية",
        head_id="emp-301",
        parent_id=EXECUTIVE_ID,
        teams=["عمليات الموظفين", "التطوير والتدريب"],
    ),
    Department(
        id="it",
        name="تقنية المعلومات",
        head_id="emp-401",
        parent_id=EXECUTIVE_ID,
        teams=["الدعم التقني", "الأمن السيبراني"],
    ),
    Department(
        id="analytics",
        name="البيانات والتحليلات",
        head_id="emp-201",
        parent_id=EXECUTIVE_ID,
        teams=["فريق التحليلات", "هندسة البيانات", "الحوكمة"],
    ),
    Department(
        id="finance",
        name="المالية",
        head_id="emp-501",
        parent_id=EXECUTIVE_ID,
        teams=["الحسابات", "المشتريات"],
    ),
    Department(
        id="operations",
        name="العمليات",
        head_id="emp-601",
        parent_id=EXECUTIVE_ID,
        teams=["المرافق", "الأمن والسلامة"],
    ),
]

# Number of employees in each team, by department id.
TEAM_SIZES: dict[str, dict[str, int]] = {
    EXECUTIVE_ID: {"الإدارة التنفيذية": 1},
    "hr": {"عمليات الموظفين": 9, "التطوير والتدريب": 5},
    "it": {"الدعم التقني": 20, "الأمن السيبراني": 12},
    "analytics": {"فريق التحليلات": 8, "هندسة البيانات": 7, "الحوكمة": 3},
    "finance": {"الحسابات": 14, "المشتريات": 8},
    "operations": {"المرافق": 90, "الأمن والسلامة": 38},
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
        "emp-101",
        "خالد السبيعي",
        "m",
        EXECUTIVE_ID,
        "الإدارة التنفيذية",
        "الرئيس التنفيذي",
        None,
        "khalid.subaie",
        "الدور 8",
    ),
    # البيانات والتحليلات
    _employee(
        "emp-201",
        "ريم الحربي",
        "f",
        "analytics",
        "فريق التحليلات",
        "مديرة البيانات والتحليلات",
        "emp-101",
        "reem.harbi",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-202",
        "فهد العنزي",
        "m",
        "analytics",
        "الحوكمة",
        "مسؤول حوكمة البيانات",
        "emp-201",
        "fahad.anazi",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-203",
        "لمى الزهراني",
        "f",
        "analytics",
        "فريق التحليلات",
        "محللة بيانات أولى",
        "emp-201",
        "lama.zahrani",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-204",
        "عمر القرني",
        "m",
        "analytics",
        "هندسة البيانات",
        "مهندس بيانات",
        "emp-201",
        "omar.qarni",
        "الدور 4 · جناح أ",
    ),
    _employee(
        "emp-205",
        "دانة الغامدي",
        "f",
        "analytics",
        "فريق التحليلات",
        "محللة بيانات",
        "emp-201",
        "dana.ghamdi",
        "الدور 4 · جناح ب",
    ),
    _employee(
        "emp-004",
        "نورة العتيبي",
        "f",
        "analytics",
        "فريق التحليلات",
        "محللة بيانات",
        "emp-201",
        "noura.otaibi",
        "الدور 4 · جناح ب",
    ),
    # الموارد البشرية
    _employee(
        "emp-301",
        "سارة القحطاني",
        "f",
        "hr",
        "عمليات الموظفين",
        "مديرة الموارد البشرية",
        "emp-101",
        "sara.qahtani",
        "الدور 2",
    ),
    _employee(
        "emp-302",
        "منصور الشمري",
        "m",
        "hr",
        "عمليات الموظفين",
        "أخصائي موارد بشرية",
        "emp-301",
        "mansour.shammari",
        "الدور 2",
    ),
    _employee(
        "emp-303",
        "هيا السالم",
        "f",
        "hr",
        "التطوير والتدريب",
        "منسقة تدريب",
        "emp-301",
        "haya.salem",
        "الدور 2",
    ),
    # تقنية المعلومات
    _employee(
        "emp-401",
        "ماجد الدوسري",
        "m",
        "it",
        "الدعم التقني",
        "مدير تقنية المعلومات",
        "emp-101",
        "majed.dosari",
        "الدور 3",
    ),
    _employee(
        "emp-402",
        "تركي العمري",
        "m",
        "it",
        "الدعم التقني",
        "مهندس دعم تقني",
        "emp-401",
        "turki.omari",
        "الدور 3",
    ),
    _employee(
        "emp-403",
        "جود الرشيد",
        "f",
        "it",
        "الأمن السيبراني",
        "محللة أمن سيبراني",
        "emp-401",
        "joud.rashid",
        "الدور 3",
    ),
    # المالية
    _employee(
        "emp-501",
        "منيرة الشهري",
        "f",
        "finance",
        "الحسابات",
        "مديرة المالية",
        "emp-101",
        "munira.shehri",
        "الدور 5",
    ),
    _employee(
        "emp-502",
        "سلطان الحارثي",
        "m",
        "finance",
        "الحسابات",
        "محاسب",
        "emp-501",
        "sultan.harthi",
        "الدور 5",
    ),
    _employee(
        "emp-503",
        "أمل الفيفي",
        "f",
        "finance",
        "المشتريات",
        "أخصائية مشتريات",
        "emp-501",
        "amal.faifi",
        "الدور 5",
    ),
    # العمليات
    _employee(
        "emp-601",
        "عبدالله المطيري",
        "m",
        "operations",
        "المرافق",
        "مدير العمليات",
        "emp-101",
        "abdullah.mutairi",
        "الدور 1",
    ),
    _employee(
        "emp-602",
        "ناصر البقمي",
        "m",
        "operations",
        "المرافق",
        "أخصائي مرافق",
        "emp-601",
        "nasser.baqami",
        "الدور 1",
    ),
    _employee(
        "emp-603",
        "ريما العسيري",
        "f",
        "operations",
        "الأمن والسلامة",
        "مسؤولة سلامة",
        "emp-601",
        "reema.asiri",
        "الدور 1",
    ),
]

# Short display names of the procedures people are responsible for. Ids are the
# document ids in data/company/manifest.json.
PROCEDURE_TITLES: dict[str, str] = {
    "annual-leave": "طلب إجازة سنوية",
    "emergency-leave": "إجازة اضطرارية",
    "remote-work": "طلب عمل عن بُعد",
    "probation": "تقييم فترة التجربة",
    "training-request": "طلب تدريب خارجي",
    "warehouse": "صلاحية بيانات المستودع",
    "classification": "تصنيف البيانات",
    "dashboards": "اعتماد لوحة مؤشرات",
    "system-access": "طلب صلاحية نظام",
    "vpn": "تفعيل VPN",
    "phishing": "الإبلاغ عن تصيّد",
    "reimbursements": "تعويض مصاريف العمل",
    "business-travel": "طلب سفر لمهمة عمل",
    "procurement": "طلب شراء أدوات",
    "id-badge": "بطاقة دخول المبنى",
    "incident": "الإبلاغ عن حادث سلامة",
}


def _topic(employee_id: str, topic: str, procedure_id: str | None = None) -> ContactResponsibility:
    return ContactResponsibility(employee_id=employee_id, topic=topic, procedure_id=procedure_id)


RESPONSIBILITIES: list[ContactResponsibility] = [
    _topic("emp-101", "استراتيجية الشركة"),
    _topic("emp-201", "اعتماد الإجازات", "annual-leave"),
    _topic("emp-201", "موافقة الصلاحيات", "warehouse"),
    _topic("emp-201", "تقييم الأداء"),
    _topic("emp-202", "حوكمة البيانات"),
    _topic("emp-202", "تصنيف البيانات", "classification"),
    _topic("emp-203", "لوحات المؤشرات", "dashboards"),
    _topic("emp-203", "Power BI"),
    _topic("emp-204", "مستودع البيانات"),
    _topic("emp-204", "خطوط معالجة البيانات"),
    _topic("emp-205", "تقارير المبيعات"),
    _topic("emp-301", "رصيد الإجازات"),
    _topic("emp-301", "الإجازة الاضطرارية", "emergency-leave"),
    _topic("emp-301", "العمل عن بعد", "remote-work"),
    _topic("emp-302", "فترة التجربة", "probation"),
    _topic("emp-302", "الرواتب والبدلات"),
    _topic("emp-303", "التدريب والدورات", "training-request"),
    _topic("emp-401", "أمن المعلومات"),
    _topic("emp-402", "صلاحيات الأنظمة", "system-access"),
    _topic("emp-402", "الاتصال الآمن VPN", "vpn"),
    _topic("emp-402", "الأجهزة والحاسب المحمول"),
    _topic("emp-403", "رسائل التصيد", "phishing"),
    _topic("emp-403", "كلمات المرور والتحقق الثنائي"),
    _topic("emp-501", "اعتماد المصروفات", "reimbursements"),
    _topic("emp-502", "تعويض المصاريف", "reimbursements"),
    _topic("emp-502", "السفر لمهام العمل", "business-travel"),
    _topic("emp-503", "طلبات الشراء", "procurement"),
    _topic("emp-601", "خدمات المكتب"),
    _topic("emp-602", "بطاقة دخول المبنى", "id-badge"),
    _topic("emp-602", "حجز القاعات"),
    _topic("emp-603", "حوادث السلامة", "incident"),
]
