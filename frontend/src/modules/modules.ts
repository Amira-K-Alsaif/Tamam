import type { LucideIcon } from 'lucide-react'
import { FileStack, Flag, ListChecks, MessageCircle, Network, TrendingUp } from 'lucide-react'

export type TamamModule = {
  id: string
  path: string
  title: string
  summary: string
  owner: number
  icon: LucideIcon
  adminOnly?: boolean
}

// The six product modules. `owner` is the team member number from docs/team.md.
export const MODULES: TamamModule[] = [
  { id: 'chat', path: '/chat', title: 'اسأل عن إجراء', summary: 'إجابات من وثائق الشركة مع مصادرها', owner: 1, icon: MessageCircle },
  { id: 'procedures', path: '/procedures', title: 'اختر الإجراء', summary: 'الخطوات والمتطلبات والنماذج لكل إجراء', owner: 3, icon: ListChecks },
  { id: 'org-map', path: '/org-map', title: 'خريطة الشركة', summary: 'الأقسام وأعضاؤها، ومين تكلّم عن أي شي', owner: 4, icon: Network },
  { id: 'onboarding', path: '/onboarding', title: 'مساري التأهيلي', summary: 'خارطة لكل اللي ناقصك: معرفة وصلاحيات وأشخاص', owner: 5, icon: Flag },
  { id: 'career', path: '/career', title: 'مساري المهني', summary: 'من منصبك الحالي إلى المنصب اللي بعده', owner: 6, icon: TrendingUp },
  { id: 'knowledge', path: '/knowledge', title: 'مصنع المعرفة', summary: 'رفع الوثائق ومعالجتها وتجهيزها للبحث', owner: 2, icon: FileStack, adminOnly: true },
]

export function moduleById(id: string): TamamModule {
  const found = MODULES.find((m) => m.id === id)
  if (!found) throw new Error(`Unknown module: ${id}`)
  return found
}
