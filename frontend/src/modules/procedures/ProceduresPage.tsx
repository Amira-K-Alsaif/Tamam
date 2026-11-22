import { useSearchParams } from 'react-router'
import { PageHeader } from '../../components/PageHeader'
import { moduleById } from '../modules'
import { FormFiller } from './FormFiller'
import { FormsSection } from './FormsSection'
import { ProcedureCatalog } from './ProcedureCatalog'
import { ProcedureDetail } from './ProcedureDetail'

// Owned by team member 3. The procedure catalog and company forms. `?id=proc-<document id>`
// opens one procedure (so other modules can link a procedure_id) and `?form=<id>` one form.
export default function ProceduresPage() {
  const info = moduleById('procedures')
  const [params] = useSearchParams()
  const id = params.get('id')
  const formId = params.get('form')

  if (id) return <ProcedureDetail key={id} id={id} />
  if (formId) return <FormFiller key={formId} id={formId} />

  return (
    <>
      <PageHeader title={info.title} description="كل إجراء في الشركة: خطواته، وش تجهّزين له، ونماذجه، ومين المسؤول عنه." />
      <ProcedureCatalog />
      <FormsSection />
    </>
  )
}
