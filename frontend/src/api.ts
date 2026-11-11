export interface Transaction {
  id: number
  date: string
  description: string
  amount: number
  category: string
}

export interface TransactionPage {
  items: Transaction[]
  total: number
  page: number
  page_size: number
}

export interface ImportResult {
  imported: number
  skipped_duplicates: number
  skipped_invalid: number
}

export interface Budget {
  id: number
  category: string
  monthly_limit: number
}

export interface BudgetStatus {
  category: string
  monthly_limit: number
  spent: number
  remaining: number
  percent_used: number
}

export interface Summary {
  month: string
  income: number
  expenses: number
  net: number
  savings_rate: number
  by_category: { category: string; total: number }[]
  budgets: BudgetStatus[]
  top_expenses: Transaction[]
}

export interface TrendPoint {
  month: string
  income: number
  expenses: number
  net: number
}

const BASE = import.meta.env.VITE_API_URL ?? ''
const TOKEN_KEY = 'finance-tracker-token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token: string | null) =>
  token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY)

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

let onUnauthorized: () => void = () => {}
export const setUnauthorizedHandler = (handler: () => void) => {
  onUnauthorized = handler
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (typeof init.body === 'string') headers.set('Content-Type', 'application/json')

  const response = await fetch(`${BASE}/api${path}`, { ...init, headers })
  if (response.status === 204) return undefined as T

  const body = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized()
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((d: { msg: string }) => d.msg).join(', ')
      : (detail ?? `Request failed (${response.status})`)
    throw new ApiError(response.status, message)
  }
  return body as T
}

const query = (params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const api = {
  register: (email: string, password: string) =>
    request<{ id: number; email: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username: email, password }),
    }),
  me: () => request<{ id: number; email: string }>('/auth/me'),

  categories: () => request<string[]>('/transactions/categories'),
  transactions: (params: {
    month?: string
    category?: string
    search?: string
    page?: number
    page_size?: number
  }) => request<TransactionPage>(`/transactions${query(params)}`),
  importCsv: (file: Blob, name = 'transactions.csv') => {
    const form = new FormData()
    form.append('file', file, name)
    return request<ImportResult>('/transactions/import', { method: 'POST', body: form })
  },
  updateCategory: (id: number, category: string) =>
    request<Transaction>(`/transactions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ category }),
    }),
  deleteTransaction: (id: number) => request<void>(`/transactions/${id}`, { method: 'DELETE' }),

  budgets: () => request<Budget[]>('/budgets'),
  saveBudget: (category: string, monthly_limit: number) =>
    request<Budget>('/budgets', { method: 'PUT', body: JSON.stringify({ category, monthly_limit }) }),
  deleteBudget: (id: number) => request<void>(`/budgets/${id}`, { method: 'DELETE' }),

  months: () => request<string[]>('/analytics/months'),
  summary: (month?: string) => request<Summary>(`/analytics/summary${query({ month })}`),
  trend: (months = 6) => request<TrendPoint[]>(`/analytics/trend${query({ months })}`),
}
