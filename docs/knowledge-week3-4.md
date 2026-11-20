# مصنع المعرفة — مهام الأسبوعين الثالث والرابع

## ما تم بناؤه

- **رفع الوثائق**: يتحقق الخادم من نوع الملف وحجمه، ثم يستخرج النص عبر Docling أو Markdown، يقسمه إلى مقاطع، يولد BGE-M3 embeddings (1024-dimensional) ويحفظ الأصل في private Supabase Storage والمقاطع في PostgreSQL/pgvector.
- **إدارة المشرف**: عرض الوثائق، الرفع والحذف مع التحقق من JWT و`app_metadata.role=admin` في الخادم، وليس بناءً على بيانات يرسلها المتصفح.
- **ترشيح تعارض السياسات**: `/api/knowledge/conflicts` يقارن عبارات متشابهة في وثيقتين جاهزتين ضمن القسم نفسه عندما يختلف حد رقمي ووحدته. كل نتيجة تحفظ نصين حرفيين ومراجع document/chunk/section. **هذه مرشحات للمراجعة، وليست إثباتًا آليًا للتعارض**. يستبعد النصوص التي تتضمن أكثر من مقدار رقمي لتقليل الأخطاء. لا يدعي شمول كل التعارضات، خاصة النصوص التي لا تستخدم أرقامًا.
- **تنبيهات التغيير**: `knowledge_change_events` وسجل أحداث عبر PostgreSQL trigger على جدول `documents`. يتتبع إضافة سياسة بحالة `ready`، تغيير عنوانها أو `updated_at`، وحذفها. `GET /api/knowledge/alerts` يعيد آخر 50 حدثًا؛ يجب تطبيق migration قبل استخدامه. **تغيير نص chunks وحده من خارج الـpipeline لا يسجل حدثًا**؛ ينبغي أن يصاحب أي تحديث لسياسة تحديث قيمة `documents.updated_at`.
- **جودة البيانات**: `/api/knowledge/quality` يدقق الوثائق والأجزاء المفقودة أو الفارغة والمكررة دون تعديل بيانات حقيقية؛ يلزم مراجعة المشرف قبل تنظيف قاعدة الإنتاج.

## المعمارية

1. Frontend `KnowledgePage` → backend API مع Bearer token لحساب Admin.
2. Backend validates file and auth → `ingestion_service` + `embedding_service`.
3. Original file → private Storage, metadata → `documents`, chunks/embedding → `chunks`.
4. Query → `match_chunks` (pgvector) → sourced responses to chat module.
5. Review endpoints read original chunk text and document metadata; policy change trigger writes event history.

## الاختبارات والتشغيل

```bash
cd backend
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
cd ../frontend
npm run build
npm run lint
npm test
```

Apply `supabase/migrations/20261120_knowledge_change_events.sql` using the Supabase project SQL editor once; do not run it on the wrong project.

## القيود والمتبقي قبل اعتماد الإنتاج

- يلزم اختبار تكامل بـSupabase حقيقي لحساب Admin وفيه upload + delete + alerts.
- تخزين الأصل وحفظ صفوف DB ليسا عملية ذرية؛ في حالات انقطاع الاتصال يُراجع المشرف اتساق التخزين.
- ترشيح التعارضات خوارزمية أولية تعتمد تقارب الألفاظ والقيم الرقمية، ويحتاج الإنسان للتأكد من السياق والاستثناءات والتواريخ.
- تنبيهات التغيير تسجل الأحداث في قاعدة البيانات؛ لا ترسل بريدًا إلكترونيًا أو Push notifications.
- تحديث محتوى سياسة قديمة يحتاج مسار عمل معتمدًا للمراجعة والإصدار، وليس مجرد رفع وثيقة جديدة مع الإبقاء على القديمة ضمن البحث.

## حالة التقييم

مجموعة الأسئلة الـ50 محفوظة من مرحلة سابقة؛ عند أي تغيير في المصادر يجب إعادة تجربة الأسئلة نفسها ومقارنة الإجابات ومراجعها. لا يُذكر معدل نجاح جديد دون تشغيل التقييم وتوثيق نتائجه.
