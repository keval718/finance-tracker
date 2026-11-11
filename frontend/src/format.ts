const currency = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' })
const wholeCurrency = new Intl.NumberFormat('en-CA', {
  style: 'currency',
  currency: 'CAD',
  maximumFractionDigits: 0,
})

export const money = (value: number) => currency.format(value)
export const moneyRounded = (value: number) => wholeCurrency.format(value)

/** "2026-03" -> "March 2026" (or "Mar" when short). */
export const monthLabel = (month: string, short = false) => {
  const [year, mon] = month.split('-').map(Number)
  const date = new Date(year, mon - 1, 1)
  return short
    ? date.toLocaleDateString('en-CA', { month: 'short' })
    : date.toLocaleDateString('en-CA', { month: 'long', year: 'numeric' })
}

/** "2026-03-05" -> "Mar 5". Parsed by hand so the timezone cannot shift the day. */
export const dayLabel = (isoDate: string) => {
  const [year, mon, day] = isoDate.split('-').map(Number)
  return new Date(year, mon - 1, day).toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })
}

export const CATEGORY_COLORS: Record<string, string> = {
  Housing: '#0f766e',
  Groceries: '#65a30d',
  Dining: '#ea580c',
  Transport: '#2563eb',
  Utilities: '#0891b2',
  Subscriptions: '#7c3aed',
  Shopping: '#db2777',
  Health: '#dc2626',
  Entertainment: '#ca8a04',
  Travel: '#4f46e5',
  Fees: '#78716c',
  Income: '#059669',
  Other: '#94a3b8',
}

export const categoryColor = (category: string) => CATEGORY_COLORS[category] ?? '#94a3b8'
