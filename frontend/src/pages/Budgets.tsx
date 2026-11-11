import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api'
import type { Budget } from '../api'
import { categoryColor, money } from '../format'

export default function Budgets() {
  const [budgets, setBudgets] = useState<Budget[] | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [category, setCategory] = useState('')
  const [limit, setLimit] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    api
      .budgets()
      .then(setBudgets)
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    load()
    api
      .categories()
      .then((all) => {
        const spending = all.filter((c) => c !== 'Income')
        setCategories(spending)
        setCategory(spending[0] ?? '')
      })
      .catch(() => {})
  }, [load])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      await api.saveBudget(category, Number(limit))
      setLimit('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save budget')
    }
  }

  const remove = async (id: number) => {
    try {
      await api.deleteBudget(id)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete budget')
    }
  }

  const existing = budgets?.some((b) => b.category === category)

  return (
    <>
      <header className="page-header">
        <h1>Budgets</h1>
      </header>

      <div className="card">
        <h2>Set a monthly limit</h2>
        <form className="filters" onSubmit={save}>
          <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <input
            type="number"
            min="1"
            step="0.01"
            placeholder="Monthly limit ($)"
            aria-label="Monthly limit in dollars"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            required
          />
          <button className="primary">{existing ? 'Update budget' : 'Add budget'}</button>
        </form>
        {error && (
          <div className="error small" role="alert">
            {error}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Your budgets</h2>
        {budgets === null ? (
          <p className="muted">Loading…</p>
        ) : budgets.length === 0 ? (
          <p className="muted">No budgets yet. Add one above and it will show on the dashboard.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th className="num">Monthly limit</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {budgets.map((b) => (
                <tr key={b.id}>
                  <td>
                    <span className="category">
                      <span className="dot" style={{ background: categoryColor(b.category) }} />
                      {b.category}
                    </span>
                  </td>
                  <td className="num">{money(b.monthly_limit)}</td>
                  <td className="num">
                    <button
                      className="link danger"
                      aria-label={`Remove ${b.category} budget`}
                      onClick={() => remove(b.id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
