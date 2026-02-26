import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import SuiteBuilder from './pages/SuiteBuilder'
import ResultDetail from './pages/ResultDetail'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="run" element={<SuiteBuilder />} />
        <Route path="results/:id" element={<ResultDetail />} />
      </Route>
    </Routes>
  )
}
