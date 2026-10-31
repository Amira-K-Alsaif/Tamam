type ProgressBarProps = {
  label: string
  // 0 to 100.
  value: number
}

const arabicPercent = new Intl.NumberFormat('ar-SA', { style: 'percent', maximumFractionDigits: 0 })

export function ProgressBar({ label, value }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between text-sm text-muted">
        <span>{label}</span>
        <span>{arabicPercent.format(clamped / 100)}</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        className="h-2 rounded-full bg-line"
      >
        <div className="h-2 rounded-full bg-aurora" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  )
}
