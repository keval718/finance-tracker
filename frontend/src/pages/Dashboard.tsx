import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api'
import type { Summary, TrendPoint } from '../api'
import ImportButtons from '../components/ImportButtons'
import { categoryColor, dayLabel, money, moneyRounded, monthLabel } from '../format'

const INCOME_COLOR = '#059669'
const EXPENSE_COLOR = '#e11d48'

export default function Dashboard() {
  const [months, setMonths] = useState<string[] | null>(null)
  const [month, setMonth] = useState<string>()
  const [summary, setSummary] = useState<Summary | null>(null)
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [error, setError] = useState<string | null>(null)

  const loadMonths = useCallback(() => {
    Promise.all([api.months(), api.trend(6)])
      .then(([available, trendPoints]) => {
        setMonths(available)
        setTrend(trendPoints)
        setMonth((current) => (current && available.includes(current) ? current : available[0]))
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(loadMonths, [loadMonths])

  useEffect(() => {
    if (!month) return
    let cancelled = false
    api
      .summary(month)
      .then((data) => !cancelled && setSummary(data))
      .catch((err) => !cancelled && setError(err.message))
    return () => {
      cancelled = true
    }
  }, [month])

  if (error) return <div className="error">{error}</div>
  if (months === null) return <div className="muted">Loading…</div>

  if (months.length === 0) {
    return (
      <div className="card empty">
        <h2>No transactions yet</h2>
        <p className="muted">
          Import a CSV export from your bank, or load six months of sample data to look around.
        </p>
        <ImportButtons onImported={loadMonths} />
      </div>
    )
  }

  if (!summary) return <div className="muted">Loading…</div>

  return (
    <>
      <header className="page-header">
        <h1>Dashboard</h1>
        <select value={month} onChange={(e) => setMonth(e.target.value)} aria-label="Month">
          {months.map((m) => (
            <option key={m} value={m}>
              {monthLabel(m)}
            </option>
          ))}
        </select>
      </header>

      <section className="tiles">
        <Tile label="Income" value={money(summary.income)} />
        <Tile label="Expenses" value={money(summary.expenses)} />
        <Tile
          label="Net"
          value={money(summary.net)}
          tone={summary.net >= 0 ? 'positive' : 'negative'}
        />
        <Tile label="Savings rate" value={`${summary.savings_rate}%`} />
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Spending by category</h2>
          {summary.by_category.length === 0 ? (
            <p className="muted">No spending this month.</p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(180, summary.by_category.length * 34)}>
              <BarChart data={summary.by_category} layout="vertical" margin={{ left: 12, right: 24 }}>
                <XAxis type="number" tickFormatter={moneyRounded} tickLine={false} axisLine={false} />
                <YAxis
                  type="category"
                  dataKey="category"
                  width={100}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip formatter={(value) => money(Number(value))} cursor={{ fill: '#f1f5f9' }} />
                <Bar dataKey="total" name="Spent" radius={[0, 4, 4, 0]} isAnimationActive={false}>
                  {summary.by_category.map((entry) => (
                    <Cell key={entry.category} fill={categoryColor(entry.category)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h2>Income vs expenses</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trend} margin={{ left: 12, right: 12 }}>
              <CartesianGrid vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="month"
                tickFormatter={(m: string) => monthLabel(m, true)}
                tickLine={false}
                axisLine={false}
              />
              <YAxis tickFormatter={moneyRounded} tickLine={false} axisLine={false} width={70} />
              <Tooltip
                formatter={(value) => money(Number(value))}
                labelFormatter={(m) => monthLabel(String(m))}
                cursor={{ fill: '#f1f5f9' }}
              />
              <Legend />
              <Bar
                dataKey="income"
                name="Income"
                fill={INCOME_COLOR}
                radius={[4, 4, 0, 0]}
                isAnimationActive={false}
              />
              <Bar
                dataKey="expenses"
                name="Expenses"
                fill={EXPENSE_COLOR}
                radius={[4, 4, 0, 0]}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Budgets</h2>
          {summary.budgets.length === 0 ? (
            <p className="muted">
              No budgets yet. <Link to="/budgets">Set a monthly limit</Link> for a category to track
              it here.
            </p>
          ) : (
            <ul className="budget-list">
              {summary.budgets.map((b) => {
                const over = b.spent > b.monthly_limit
                return (
                  <li key={b.category}>
                    <div className="row">
                      <span>{b.category}</span>
                      <span className={over ? 'negative' : 'muted'}>
                        {money(b.spent)} of {money(b.monthly_limit)}
                        {over && ` · ${money(-b.remaining)} over`}
                      </span>
                    </div>
                    <div
                      className="progress"
                      role="progressbar"
                      aria-label={`${b.category} budget used`}
                      aria-valuenow={Math.round(b.percent_used)}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
                      <div
                        className={over ? 'over' : b.percent_used >= 85 ? 'warn' : ''}
                        style={{ width: `${Math.min(100, b.percent_used)}%` }}
                      />
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <div className="card">
          <h2>Largest expenses</h2>
          <table className="compact">
            <tbody>
              {summary.top_expenses.map((tx) => (
                <tr key={tx.id}>
                  <td className="muted nowrap">{dayLabel(tx.date)}</td>
                  <td>{tx.description}</td>
                  <td className="num">{money(-tx.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

function Tile({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="card tile">
      <div className="muted small">{label}</div>
      <div className={`tile-value ${tone ?? ''}`}>{value}</div>
    </div>
  )
}
