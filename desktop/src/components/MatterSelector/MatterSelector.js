import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useChatStore } from '../../stores/chatStore';
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';
export function MatterSelector() {
    const [matters, setMatters] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const token = useAuthStore((s) => s.token);
    const activeMatter = useChatStore((s) => s.activeMatter);
    const setActiveMatter = useChatStore((s) => s.setActiveMatter);
    useEffect(() => {
        const fetchMatters = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const headers = { 'Content-Type': 'application/json' };
                if (token)
                    headers['Authorization'] = `Bearer ${token}`;
                const response = await fetch(`${API_BASE_URL}/matters`, { headers });
                if (!response.ok) {
                    throw new Error('Failed to load matters');
                }
                const body = await response.json();
                setMatters(body.data);
            }
            catch (err) {
                setError(err instanceof Error ? err.message : 'Error loading matters');
            }
            finally {
                setIsLoading(false);
            }
        };
        void fetchMatters();
    }, [token]);
    if (isLoading) {
        return _jsx("div", { className: "matter-selector", children: "Loading matters..." });
    }
    if (error) {
        return _jsxs("div", { className: "matter-selector error", children: ["Error: ", error] });
    }
    return (_jsxs("div", { className: "matter-selector", children: [_jsx("h3", { children: "Your Matters" }), _jsx("ul", { role: "listbox", children: matters.map((matter) => (_jsxs("li", { role: "option", "aria-selected": activeMatter?.id === matter.id, onClick: () => setActiveMatter(matter), style: { cursor: 'pointer', fontWeight: activeMatter?.id === matter.id ? 'bold' : 'normal' }, children: [matter.title, _jsxs("span", { className: "case-number", children: [" (", matter.caseNumber, ")"] })] }, matter.id))) })] }));
}
