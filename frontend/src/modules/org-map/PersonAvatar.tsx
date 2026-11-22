import type { PersonSummary } from './orgMapApi'

// Avatars cycle through the brand colors so neighbours look different.
const TONES = ['bg-teal', 'bg-blue', 'bg-mint', 'bg-faint']

const SIZES = { sm: 'size-10 text-sm', lg: 'size-16 text-xl' }

function tone(id: string): string {
  const sum = [...id].reduce((total, char) => total + char.charCodeAt(0), 0)
  return TONES[sum % TONES.length]
}

export function PersonAvatar({ person, size = 'sm' }: { person: PersonSummary; size?: 'sm' | 'lg' }) {
  // The viewer's own avatar uses the aurora, like the side menu.
  const color = person.relation === 'self' ? 'bg-aurora' : tone(person.id)
  return (
    <span
      aria-hidden
      className={`flex shrink-0 items-center justify-center rounded-full font-semibold text-night ${SIZES[size]} ${color}`}
    >
      {person.full_name[0]}
    </span>
  )
}
