import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import {
  getDepartment,
  getOverview,
  getPerson,
  searchPeople,
  type DepartmentDetail,
  type OrgOverview,
  type PersonDetail,
  type SearchResponse,
} from './orgMapApi'

type Load<T> = { data: T | null; loading: boolean; error: boolean }

const IDLE = { data: null, loading: false, error: false }

/** Loads `fetcher(id)` whenever `id` (or `attempt`) changes, ignoring answers that arrive late.
 * While a new answer loads, the previous data stays on screen. */
function useLoad<T>(id: string | null, fetcher: (id: string) => Promise<T>, attempt = 0): Load<T> {
  const key = id === null ? null : `${id}:${attempt}`
  const [state, setState] = useState<{ key: string | null; data: T | null; error: boolean }>({
    key: null,
    data: null,
    error: false,
  })

  useEffect(() => {
    if (id === null) return
    let current = true
    const loadedKey = `${id}:${attempt}`
    fetcher(id)
      .then((data) => current && setState({ key: loadedKey, data, error: false }))
      .catch(() => current && setState({ key: loadedKey, data: null, error: true }))
    return () => {
      current = false
    }
  }, [id, fetcher, attempt])

  if (key === null) return IDLE
  return { data: state.data, loading: state.key !== key, error: state.key === key && state.error }
}

const overviewKey = 'overview'

/** The company map's state: the overview, the open department and person, and search. */
export function useOrgMap() {
  const [attempt, setAttempt] = useState(0)
  const overview = useLoad<OrgOverview>(overviewKey, getOverview, attempt)
  // Other modules link `?person=<employee id>` (e.g. «أشخاص تقابلهم» in onboarding).
  const [params] = useSearchParams()
  const linkedPerson = params.get('person')
  // Until the viewer picks something, show the linked person, or their own manager.
  const [chosenDepartment, setDepartmentId] = useState<string | null>(null)
  const [chosenPerson, setPersonId] = useState<string | null>(null)
  const personId = chosenPerson ?? linkedPerson ?? overview.data?.my_manager_id ?? null
  const person = useLoad<PersonDetail>(personId, getPerson, attempt)
  // A linked person opens in their own department once their card has loaded.
  const linkedDepartment = linkedPerson && person.data?.id === linkedPerson ? person.data.department_id : null
  const departmentId = chosenDepartment ?? linkedDepartment ?? overview.data?.my_department_id ?? null
  const department = useLoad<DepartmentDetail>(departmentId, getDepartment, attempt)

  const [search, setSearch] = useState<Load<SearchResponse>>(IDLE)

  const openDepartment = useCallback((id: string) => setDepartmentId(id), [])

  const openPerson = useCallback((id: string, inDepartment?: string) => {
    setPersonId(id)
    if (inDepartment) setDepartmentId(inDepartment)
  }, [])

  const runSearch = useCallback(async (query: string) => {
    const text = query.trim()
    if (text.length < 2) return
    setSearch({ data: null, loading: true, error: false })
    try {
      setSearch({ data: await searchPeople(text), loading: false, error: false })
    } catch {
      setSearch({ data: null, loading: false, error: true })
    }
  }, [])

  const clearSearch = useCallback(() => setSearch(IDLE), [])
  const retry = useCallback(() => setAttempt((n) => n + 1), [])

  return {
    overview,
    department,
    person,
    departmentId,
    personId,
    search,
    openDepartment,
    openPerson,
    runSearch,
    clearSearch,
    retry,
  }
}
