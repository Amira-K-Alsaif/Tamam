import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Button } from '../../components/Button'
import { PageHeader } from '../../components/PageHeader'
import { DepartmentPanel } from './DepartmentPanel'
import { OrgChart } from './OrgChart'
import { PersonPanel } from './PersonPanel'
import { SearchResults } from './SearchResults'
import { useOrgMap } from './useOrgMap'

/** «خريطة الشركة»: departments and their people, and who to talk to about what. */
export default function OrgMapPage() {
  const map = useOrgMap()
  const [query, setQuery] = useState('')
  const overview = map.overview.data

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void map.runSearch(query)
  }

  const searchForm = (
    <form
      role="search"
      onSubmit={submit}
      className="flex h-12 w-full max-w-md items-center gap-3 rounded-2xl border border-line bg-surface px-4 focus-within:border-mint"
    >
      <label htmlFor="org-search" className="sr-only">
        ابحث عن شخص حسب الموضوع
      </label>
      <input
        id="org-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="مين أكلّم عن صلاحيات البيانات؟"
        className="min-w-0 flex-1 bg-transparent text-sm text-ink outline-none"
      />
      <button type="submit" aria-label="بحث" className="text-faint hover:text-mint">
        <Search aria-hidden className="size-5" strokeWidth={1.8} />
      </button>
    </form>
  )

  const description = overview
    ? `${overview.departments.length} أقسام · ${overview.employee_count} موظف. اعرف مين في كل قسم، ومين تكلّم عن أي شي.`
    : 'الأقسام وأعضاؤها، ومين تكلّم عن أي شي.'

  return (
    <>
      <PageHeader title="خريطة الشركة" description={description} actions={searchForm} />

      <SearchResults
        result={map.search.data}
        loading={map.search.loading}
        error={map.search.error}
        onPick={(personId, departmentId) => map.openPerson(personId, departmentId)}
        onClear={map.clearSearch}
      />

      {map.overview.error && (
        <div role="alert" className="flex flex-wrap items-center gap-4 rounded-3xl border border-line bg-surface p-6">
          <p className="m-0 text-sm text-danger">تعذّر تحميل خريطة الشركة. تأكد إن الخادم شغال.</p>
          <Button variant="secondary" onClick={map.retry}>
            حاول مرة ثانية
          </Button>
        </div>
      )}

      {!overview && !map.overview.error && <p className="m-0 text-sm text-faint">جارٍ تحميل خريطة الشركة…</p>}

      {overview && (
        <div className="flex flex-wrap items-start gap-6">
          <OrgChart
            overview={overview}
            departmentId={map.departmentId}
            onDepartment={map.openDepartment}
            onPerson={(id) => map.openPerson(id)}
          >
            {map.department.error && (
              <p role="alert" className="m-0 text-sm text-danger">
                تعذّر تحميل أعضاء القسم. اختر القسم مرة ثانية.
              </p>
            )}
            {map.department.data && (
              <DepartmentPanel
                department={map.department.data}
                personId={map.personId}
                onPerson={(id) => map.openPerson(id)}
              />
            )}
          </OrgChart>

          <PersonPanel person={map.person.data} loading={map.person.loading} error={map.person.error} />
        </div>
      )}
    </>
  )
}
