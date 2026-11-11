import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { TransactionPage } from '../api'
import ImportButtons from '../components/ImportButtons'
import { categoryColor, dayLabel, money, monthLabel } from '../format'

const PAGE_SIZE = 15

export default function Transactions() {
  const [categories, setCategories] = useState<string[]>([])
  const [months, setMonths] = useState<string[]>([])
  const [month, setMonth] = useState('')
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<TransactionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    api.months().then(setMonths).catch(() => {})
  }, [refresh])

  // Wait until typing pauses before hitting the API.
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    let cancelled = false
    api
      .transactions({ month, category, search: debouncedSearch, page, page_size: PAGE_SIZE })
      .then((result) => {
        if (cancelled) return
        // If the last row of the last page was deleted, step back a page.
        if (result.items.length === 0 && page > 1) setPage(page - 1)
        else setData(result)
      })
      .catch((err) => !cancelled && setError(err.message))
    return () => {
      cancelled = true
    }
  }, [month, category, debouncedSearch, page, refresh])

  const reload = useCallback(() => setRefresh((n) => n + 1), [])

  const changeCategory = async (id: number, next: string) => {
    try {
      await api.updateCategory(id, next)
      reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  const remove = async (id: number) => {
    try {
      await api.deleteTransaction(id)
      reload()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <>
      <header className="page-header">
        <h1>Transactions</h1>
        <ImportButtons onImported={reload} />
      </header>

      <div className="card">
        <div className="filters">
          <input
            type="search"
            placeholder="Search descriptions"
            aria-label="Search descriptions"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            value={month}
            aria-label="Month"
            onChange={(e) => {
              setMonth(e.target.value)
              setPage(1)
            }}
          >
            <option value="">All months</option>
            {months.map((m) => (
              <option key={m} value={m}>
                {monthLabel(m)}
              </option>
            ))}
          </select>
          <select
            value={category}
            aria-label="Category"
            onChange={(e) => {
              setCategory(e.target.value)
              setPage(1)
            }}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>

        {error && (
          <div className="error small" role="alert">
            {error}
          </div>
        )}

        {!data ? (
          <p className="muted">Loading…</p>
        ) : data.total === 0 ? (
          <p className="muted">No transactions match.</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Category</th>
                  <th className="num">Amount</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.items.map((tx) => (
                  <tr key={tx.id}>
                    <td className="muted nowrap">{dayLabel(tx.date)}</td>
                    <td>{tx.description}</td>
                    <td>
                      <span className="category">
                        <span className="dot" style={{ background: categoryColor(tx.category) }} />
                        <select
                          className="inline"
                          value={tx.category}
                          aria-label={`Category for ${tx.description}`}
                          onChange={(e) => changeCategory(tx.id, e.target.value)}
                        >
                          {categories.map((c) => (
                            <option key={c}>{c}</option>
                          ))}
                        </select>
                      </span>
                    </td>
                    <td className={`num ${tx.amount > 0 ? 'positive' : ''}`}>
                      {tx.amount > 0 ? '+' : ''}
                      {money(tx.amount)}
                    </td>
                    <td className="num">
                      <button
                        className="link danger"
                        aria-label={`Delete ${tx.description}`}
                        onClick={() => remove(tx.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pagination">
              <span className="muted small">
                {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, data.total)} of{' '}
                {data.total}
              </span>
              <div>
                <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  Previous
                </button>
                <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}
