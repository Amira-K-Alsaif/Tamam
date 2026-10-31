import type { ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router'

// primary: the main action on a screen. secondary: everything else.
// ai: actions the assistant performs for the user (fill a form, rebuild a plan).
export type ButtonVariant = 'primary' | 'secondary' | 'ai'

const BASE =
  'inline-flex h-11 items-center justify-center gap-2 rounded-full px-5 text-sm transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50'

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-mint font-semibold text-night',
  secondary: 'border border-line-strong text-ink',
  ai: 'bg-aurora font-semibold text-night',
}

function classes(variant: ButtonVariant, className?: string) {
  return [BASE, VARIANTS[variant], className].filter(Boolean).join(' ')
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }

export function Button({ variant = 'primary', className, type = 'button', ...props }: ButtonProps) {
  return <button type={type} className={classes(variant, className)} {...props} />
}

type ButtonLinkProps = LinkProps & { variant?: ButtonVariant }

export function ButtonLink({ variant = 'primary', className, ...props }: ButtonLinkProps) {
  return <Link className={classes(variant, className as string | undefined)} {...props} />
}
