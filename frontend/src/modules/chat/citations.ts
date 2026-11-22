/**
 * The answer as the employee reads it. The backend keeps [1], [2] in the text to check that
 * every statement has a real source; the sources themselves are listed beside the answer.
 */
export function withoutCitationNumbers(answer: string): string {
  return answer.replace(/\s*\[\d+\]/g, '')
}
