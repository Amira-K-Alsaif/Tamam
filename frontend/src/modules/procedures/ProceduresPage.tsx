import { useSearchParams } from 'react-router'
import { PageHeader } from '../../components/PageHeader'
import { moduleById } from '../modules'
import { ProcedureCatalog } from './ProcedureCatalog'
import { ProcedureDetail } from './ProcedureDetail'

// Owned by team member 3. The procedure catalog; `?id=proc-<document id>` opens one procedure,
// so other modules can link straight to a procedure_id. See docs/team.md.
export default function ProceduresPage() {
  const info = moduleById('procedures')
  const [params] = useSearchParams()
  const id = params.get('id')

  if (id) return <ProcedureDetail key={id} id={id} />

  return (
    <>
      <PageHeader title={info.title} description="كل إجراء في الشركة: خطواته، وش تجهّزين له، ونماذجه، ومين المسؤول عنه." />
      <ProcedureCatalog />
    </>
  )
}
