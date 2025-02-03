import { Suspense } from 'react'
import { Loading } from './components'
import ModulePage from './module/page'

export default function Home() {
  return (
    <Suspense fallback={<Loading />}>
      <ModulePage />
    </Suspense>
  )
}
