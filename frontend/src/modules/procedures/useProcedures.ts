import { useEffect, useState } from 'react'
import { ApiError } from '../../lib/api'
import {
  getForm,
  getProcedure,
  listForms,
  listProcedures,
  type CompanyForm,
  type Procedure,
} from './proceduresApi'

const SEARCH_DELAY_MS = 250

export type CatalogState =
  | { kind: 'loading' }
  | { kind: 'error' }
  | { kind: 'ready'; procedures: Procedure[] }

/**
 * The catalog filtered by search text and department. The backend does the matching so
 * Arabic spelling variants (إجازة / اجازة) are treated the same.
 */
export function useProcedureCatalog(query: string, department: string | null) {
  const [state, setState] = useState<CatalogState>({ kind: 'loading' })
  const [departments, setDepartments] = useState<string[]>([])

  useEffect(() => {
    let cancelled = false
    listProcedures()
      .then((all) => {
        if (!cancelled) setDepartments([...new Set(all.map((p) => p.department))].sort())
      })
      .catch(() => {
        // The filtered request below reports the error.
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    // While a new search runs, the previous results stay on screen.
    let cancelled = false
    const timer = setTimeout(
      () => {
        listProcedures({ query, department })
          .then((procedures) => {
            if (!cancelled) setState({ kind: 'ready', procedures })
          })
          .catch(() => {
            if (!cancelled) setState({ kind: 'error' })
          })
      },
      query ? SEARCH_DELAY_MS : 0,
    )
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [query, department])

  return { state, departments }
}

export type ProcedureState =
  | { kind: 'loading' }
  | { kind: 'not-found' }
  | { kind: 'error' }
  | { kind: 'ready'; procedure: Procedure }

/** One procedure by id. Callers key the component by id, so a new id starts from "loading". */
export function useProcedure(id: string) {
  const [state, setState] = useState<ProcedureState>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false
    getProcedure(id)
      .then((procedure) => {
        if (!cancelled) setState({ kind: 'ready', procedure })
      })
      .catch((error: unknown) => {
        if (cancelled) return
        setState({ kind: error instanceof ApiError && error.status === 404 ? 'not-found' : 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [id])

  return state
}

export type FormsState = { kind: 'loading' } | { kind: 'error' } | { kind: 'ready'; forms: CompanyForm[] }

export function useCompanyForms(): FormsState {
  const [state, setState] = useState<FormsState>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false
    listForms()
      .then((forms) => {
        if (!cancelled) setState({ kind: 'ready', forms })
      })
      .catch(() => {
        if (!cancelled) setState({ kind: 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return state
}

export type FormState =
  | { kind: 'loading' }
  | { kind: 'not-found' }
  | { kind: 'error' }
  | { kind: 'ready'; form: CompanyForm }

/** One form by id. Callers key the component by id, so a new id starts from "loading". */
export function useCompanyForm(id: string): FormState {
  const [state, setState] = useState<FormState>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false
    getForm(id)
      .then((form) => {
        if (!cancelled) setState({ kind: 'ready', form })
      })
      .catch((error: unknown) => {
        if (cancelled) return
        setState({ kind: error instanceof ApiError && error.status === 404 ? 'not-found' : 'error' })
      })
    return () => {
      cancelled = true
    }
  }, [id])

  return state
}
