import type { GapSkill } from './api'

const SIZE = 420
const CENTER = SIZE / 2
const RADIUS = 130
const MAX_LEVEL = 5

function point(index: number, count: number, level: number): [number, number] {
  const angle = -Math.PI / 2 + (2 * Math.PI * index) / count
  const r = (RADIUS * level) / MAX_LEVEL
  return [CENTER + r * Math.cos(angle), CENTER + r * Math.sin(angle)]
}

function polygon(skills: GapSkill[], level: (s: GapSkill, i: number) => number): string {
  return skills.map((s, i) => point(i, skills.length, level(s, i)).join(',')).join(' ')
}

// Each axis is a skill; the two shapes are the target title's expected level and the
// employee's current level, both out of 5.
export function GapRadar({ skills }: { skills: GapSkill[] }) {
  const count = skills.length
  return (
    <figure className="m-0 flex flex-col items-center gap-3">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="w-full max-w-md"
        role="img"
        aria-label="رادار الفجوة بين مستواك والمستوى المطلوب"
      >
        {[1, 2, 3, 4, 5].map((level) => (
          <polygon key={level} points={polygon(skills, () => level)} className="fill-none stroke-line-strong" />
        ))}
        {skills.map((s, i) => {
          const [x, y] = point(i, count, MAX_LEVEL)
          const [lx, ly] = point(i, count, MAX_LEVEL + 1.15)
          return (
            <g key={s.skill_id}>
              <line x1={CENTER} y1={CENTER} x2={x} y2={y} className="stroke-line-strong" />
              <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" className="fill-soft text-xs">
                {s.label_ar}
              </text>
            </g>
          )
        })}
        <polygon
          points={polygon(skills, (s) => s.expected_level)}
          className="fill-mint/15 stroke-mint"
          strokeWidth={2}
        />
        <polygon
          points={polygon(skills, (s) => s.employee_level)}
          className="fill-blue/30 stroke-blue-soft"
          strokeWidth={2}
        />
      </svg>
      <figcaption className="flex flex-wrap justify-center gap-5 text-sm text-muted">
        <span className="inline-flex items-center gap-2">
          <span aria-hidden className="size-3 rounded-sm bg-mint" />
          المطلوب للمنصب المستهدف
        </span>
        <span className="inline-flex items-center gap-2">
          <span aria-hidden className="size-3 rounded-sm bg-blue-soft" />
          مستواك الحالي
        </span>
      </figcaption>
    </figure>
  )
}
