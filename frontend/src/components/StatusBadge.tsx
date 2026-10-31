export type Status = 'done' | 'in-progress' | 'missing' | 'failed'

const STYLES: Record<Status, { label: string; className: string }> = {
  done: { label: 'مكتمل', className: 'bg-mint/12 text-mint' },
  'in-progress': { label: 'قيد التنفيذ', className: 'bg-blue/18 text-blue-soft' },
  missing: { label: 'ناقص', className: 'bg-warning/16 text-warning' },
  failed: { label: 'تعذّر', className: 'bg-danger/16 text-danger' },
}

type StatusBadgeProps = {
  status: Status
  // Overrides the default wording, e.g. "مفعّلة" for an access item.
  label?: string
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const style = STYLES[status]
  return (
    <span
      className={`inline-flex h-7 shrink-0 items-center rounded-full px-3 text-xs ${style.className}`}
    >
      {label ?? style.label}
    </span>
  )
}
