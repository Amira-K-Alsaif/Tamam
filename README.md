# تمّام · Tamam

رفيقك الذكي لفهم أنظمة الشركة والوصول للمعلومة بسهولة. من أول سؤال في يومك الأول… إلى المنصب اللي بعده.

- **الواجهة:** React + Vite + TypeScript + Tailwind (`frontend/`)
- **الخادم:** FastAPI + Python (`backend/`)
- **البيانات:** Supabase (PostgreSQL + pgvector)

قواعد المشروع كلها في [`CLAUDE.md`](CLAUDE.md)، وتوزيع الوحدات والعقود المشتركة في [`docs/team.md`](docs/team.md).

---

## التشغيل محلياً

### المتطلبات

- Node.js `24.20.0` (موجود في `.nvmrc`)
- Python `3.13` أو أحدث

### الواجهة

```bash
cd frontend
npm ci
npm run dev
```

تفتح على http://localhost:5173

### الخادم

```bash
cd backend
python -m venv .venv
```

فعّلي البيئة (Windows: `.venv\Scripts\activate`، Mac/Linux: `source .venv/bin/activate`) ثم:

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

تأكدي إنه شغال: http://localhost:8000/api/health، وتوثيق الـ API على http://localhost:8000/docs

> على Windows إذا فشل إنشاء البيئة بسبب طول المسار، حطي المشروع في مسار قصير مثل `C:\code\Tamam`.

### الفحوصات قبل أي PR

```bash
cd frontend && npm run lint && npm test && npm run build
```

```bash
cd backend && ruff check . && ruff format --check . && pytest
```

---

## طريقة الشغل

1. اسحبي آخر نسخة من `main`، وافتحي فرع باسم وحدتك: `feat/chat/citations`
2. اشتغلي داخل مجلد وحدتك فقط (`backend/app/modules/<وحدتك>` و `frontend/src/modules/<وحدتك>`)
3. افتحي Pull Request على `main`
4. شيئين مطلوبين قبل الدمج:
   - **CI**: يشغّل lint والاختبارات والـ build للواجهة والخادم. لازم يكون أخضر.
   - **مراجعة زميلة**: وحدة من البنات تراجع وتوافق.
5. بعدها ادمجي في `main`.

ممنوع الدفع المباشر على `main`.

---

## حماية `main`

من **Settings ← Rules ← Rulesets** أنشئي قاعدة على `main` تمنع الدفع المباشر وتشترط PR بموافقة واحدة ونجاح فحوصات CI (`Frontend` و `Backend`).

> في الريبو الخاص، القواعد تحتاج GitHub Pro. حسابات الطلاب تحصل عليه مجاناً من GitHub Student Developer Pack.
