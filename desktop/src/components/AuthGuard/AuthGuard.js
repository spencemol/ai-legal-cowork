import { Fragment as _Fragment, jsx as _jsx } from "react/jsx-runtime";
import { useAuthStore } from '../../stores/authStore';
export function AuthGuard({ children, fallback }) {
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
    if (!isAuthenticated) {
        return _jsx(_Fragment, { children: fallback });
    }
    return _jsx(_Fragment, { children: children });
}
