import type { ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="m-0 font-display text-3xl font-extrabold">{title}</h1>
        {description && <p className="m-0 text-faint">{description}</p>}
      </div>
      {actions}
    </header>
  )
}
