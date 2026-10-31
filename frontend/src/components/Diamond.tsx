// The brand mark from the logo's two dots: a list bullet and a "done" marker.
type DiamondProps = {
  tone?: 'mint' | 'teal' | 'blue'
  filled?: boolean
}

const TONES = {
  mint: { fill: 'bg-mint', border: 'border-mint' },
  teal: { fill: 'bg-teal', border: 'border-teal' },
  blue: { fill: 'bg-blue', border: 'border-blue' },
}

export function Diamond({ tone = 'mint', filled = true }: DiamondProps) {
  const style = TONES[tone]
  return (
    <span
      aria-hidden="true"
      className={`inline-block size-2.5 shrink-0 rotate-45 ${filled ? style.fill : `border-2 ${style.border}`}`}
    />
  )
}
