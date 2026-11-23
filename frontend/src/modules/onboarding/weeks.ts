const ORDINALS = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس', 'السابع', 'الثامن', 'التاسع', 'العاشر']

// Weeks as words and tasks as a counted noun, so the tab does not read as two bare numbers.
export function weekName(week: number): string {
  return `الأسبوع ${ORDINALS[week - 1] ?? week}`
}

export function taskCount(count: number): string {
  if (count === 1) return 'مهمة وحدة'
  if (count === 2) return 'مهمتين'
  return count <= 10 ? `${count} مهام` : `${count} مهمة`
}
