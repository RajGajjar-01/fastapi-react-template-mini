import { useShallow } from 'zustand/react/shallow'
import { useAuthStore } from '@/stores/useAuthStore'

export function useAuth() {
  return useAuthStore(
    useShallow((state) => ({
      user: state.user,
      loading: state.loading,
      error: state.error,
      login: state.login,
      logout: state.logout,
      updateProfile: state.updateProfile,
      initialize: state.initialize,
    })),
  )
}
