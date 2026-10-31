import { moduleById } from '../modules/modules'
import { Card } from './Card'
import { Diamond } from './Diamond'
import { PageHeader } from './PageHeader'

const DESIGN_URL = 'https://claude.ai/artifact/HgaMHyE9pcE3qRGCWjXqPB'

// Starting point for a module page. Its owner replaces this with the real screen.
export function ModuleStarter({ moduleId }: { moduleId: string }) {
  const info = moduleById(moduleId)
  return (
    <>
      <PageHeader title={info.title} description={info.summary} />
      <Card>
        <div className="flex items-center gap-3">
          <Diamond filled={false} />
          <strong>هذي الصفحة تبنيها صاحبة الوحدة {info.owner}</strong>
        </div>
        <p className="m-0 text-muted">
          التصميم المرجعي في{' '}
          <a href={DESIGN_URL} target="_blank" rel="noreferrer" className="text-mint">
            لوحة تصميم تمّام
          </a>
          ، شاشة «{info.title}».
        </p>
      </Card>
    </>
  )
}
