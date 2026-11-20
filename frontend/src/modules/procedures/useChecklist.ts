import { useState } from 'react'

function read(key: string): string[] {
  try {
    const saved: unknown = JSON.parse(localStorage.getItem(key) ?? '[]')
    return Array.isArray(saved) ? saved.filter((item): item is string => typeof item === 'string') : []
  } catch {
    return []
  }
}

function write(key: string, items: string[]) {
  try {
    localStorage.setItem(key, JSON.stringify(items))
  } catch {
    // Private mode or blocked storage: the checklist still works for this visit.
  }
}

/** Ticked items for one checklist, remembered in this browser so the employee can come back later. */
export function useChecklist(key: string) {
  const storageKey = `tamam.procedures.${key}`
  const [checked, setChecked] = useState<string[]>(() => read(storageKey))

  function update(next: string[]) {
    setChecked(next)
    write(storageKey, next)
  }

  return {
    isChecked: (item: string) => checked.includes(item),
    toggle: (item: string) =>
      update(checked.includes(item) ? checked.filter((i) => i !== item) : [...checked, item]),
    check: (item: string) => {
      if (!checked.includes(item)) update([...checked, item])
    },
    reset: () => update([]),
  }
}
