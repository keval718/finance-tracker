import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api, getToken, setToken, setUnauthorizedHandler } from './api'
import { AuthContext } from './auth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(null)
  const [loading, setLoading] = useState(Boolean(getToken()))

  const logout = useCallback(() => {
    setToken(null)
    setEmail(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (!getToken()) return
    api
      .me()
      .then((user) => setEmail(user.email))
      .catch(logout)
      .finally(() => setLoading(false))
  }, [logout])

  const login = useCallback(async (userEmail: string, password: string) => {
    const { access_token } = await api.login(userEmail, password)
    setToken(access_token)
    setEmail((await api.me()).email)
  }, [])

  const register = useCallback(
    async (userEmail: string, password: string) => {
      await api.register(userEmail, password)
      await login(userEmail, password)
    },
    [login],
  )

  const value = useMemo(
    () => ({ email, loading, login, register, logout }),
    [email, loading, login, register, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
