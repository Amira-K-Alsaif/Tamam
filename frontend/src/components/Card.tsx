import type { ReactNode } from 'react'

type CardProps = {
  title?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function Card({ title, action, children, className }: CardProps) {
  return (
    <section
      className={['flex flex-col gap-4 rounded-3xl border border-line bg-surface p-6', className]
        .filter(Boolean)
        .join(' ')}
    >
      {(title || action) && (
        <div className="flex items-center justify-between gap-3">
          {title && <h2 className="m-0 font-display text-lg font-semibold">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  )
}
