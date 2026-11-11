import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Layout from './components/Layout'
import Budgets from './pages/Budgets'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Transactions from './pages/Transactions'

export default function App() {
  const { email, loading } = useAuth()

  if (loading) return <div className="center-screen muted">Loading…</div>
  if (!email) return <Login />

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/budgets" element={<Budgets />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
