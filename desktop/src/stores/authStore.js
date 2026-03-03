import { create } from 'zustand';
export const useAuthStore = create()((set, get) => ({
    token: null,
    user: null,
    login: (token, user) => set({ token, user }),
    logout: () => set({ token: null, user: null }),
    isAuthenticated: () => get().token !== null,
}));
