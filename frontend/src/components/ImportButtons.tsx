import { useRef, useState } from 'react'
import { api } from '../api'
import type { ImportResult } from '../api'

/** "Import CSV" and "Load sample data" buttons, with a result message. */
export default function ImportButtons({ onImported }: { onImported: () => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null)

  const run = async (load: () => Promise<ImportResult>) => {
    setBusy(true)
    setMessage(null)
    try {
      const result = await load()
      const parts = [`Imported ${result.imported} transactions`]
      if (result.skipped_duplicates) parts.push(`${result.skipped_duplicates} duplicates skipped`)
      if (result.skipped_invalid) parts.push(`${result.skipped_invalid} invalid rows skipped`)
      setMessage({ text: parts.join(' · ') })
      onImported()
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : 'Import failed', error: true })
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  const loadSample = () =>
    run(async () => {
      const response = await fetch('/sample_transactions.csv')
      return api.importCsv(await response.blob(), 'sample_transactions.csv')
    })

  return (
    <div className="import">
      <input
        ref={input}
        type="file"
        accept=".csv,text/csv"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) run(() => api.importCsv(file, file.name))
        }}
      />
      <button className="primary" disabled={busy} onClick={() => input.current?.click()}>
        {busy ? 'Importing…' : 'Import CSV'}
      </button>
      <button disabled={busy} onClick={loadSample}>
        Load sample data
      </button>
      {message && (
        <span className={message.error ? 'error small' : 'success small'} role="status">
          {message.text}
        </span>
      )}
    </div>
  )
}
