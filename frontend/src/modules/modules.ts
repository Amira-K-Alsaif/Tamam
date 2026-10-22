import type { LucideIcon } from 'lucide-react'
import { BookOpen, Compass, FileStack, MessageCircle, Network, TrendingUp } from 'lucide-react'

export type TamamModule = {
  id: string
  title: string
  summary: string
  owner: number
  icon: LucideIcon
}

// The six product modules. `owner` is the team member number from docs/team.md.
export const MODULES: TamamModule[] = [
  { id: 'chat', title: 'اسأل عن إجراء', summary: 'إجابات من وثائق الشركة مع مصادرها', owner: 1, icon: MessageCircle },
  { id: 'knowledge', title: 'مصنع المعرفة', summary: 'رفع الوثائق ومعالجتها وتجهيزها للبحث', owner: 2, icon: FileStack },
  { id: 'procedures', title: 'اختر الإجراء', summary: 'الخطوات والمتطلبات والنماذج لكل إجراء', owner: 3, icon: BookOpen },
  { id: 'procedure-map', title: 'خريطة الإجراءات', summary: 'كيف ترتبط الإجراءات بالسياسات والأقسام', owner: 4, icon: Network },
  { id: 'onboarding', title: 'مساري التأهيلي', summary: 'مسار يتكيّف مع قسمك ونتائجك', owner: 5, icon: Compass },
  { id: 'career', title: 'مساري المهني', summary: 'من منصبك الحالي إلى المنصب اللي بعده', owner: 6, icon: TrendingUp },
]
