import type { ReactNode } from 'react'
import { useAuthStore } from '../../stores/authStore'

interface AuthGuardProps {
  children: ReactNode
  fallback: ReactNode
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())

  if (!isAuthenticated) {
    return <>{fallback}</>
  }

  return <>{children}</>
}
