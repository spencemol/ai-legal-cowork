import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { saveToken } from '../../services/tokenStorage';
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';
export function LoginPage({ onLoginSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [ssoConfig, setSsoConfig] = useState(null);
    const [ssoLoading, setSsoLoading] = useState(true);
    const login = useAuthStore((s) => s.login);
    // Fetch SSO config on mount (Task 9.2)
    useEffect(() => {
        async function fetchSsoConfig() {
            try {
                const response = await fetch(`${API_BASE_URL}/auth/sso/config`);
                if (response.ok) {
                    const config = await response.json();
                    setSsoConfig(config);
                }
            }
            catch {
                // SSO config fetch failed — default to password-only
                setSsoConfig({ sso_enabled: false, provider: null, strategy: 'password' });
            }
            finally {
                setSsoLoading(false);
            }
        }
        void fetchSsoConfig();
    }, []);
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            if (!response.ok) {
                const body = await response.json().catch(() => ({ error: 'Login failed' }));
                throw new Error(body.error ?? 'Login failed');
            }
            const data = await response.json();
            await saveToken(data.token);
            login(data.token, data.user);
            onLoginSuccess();
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
        }
        finally {
            setIsLoading(false);
        }
    };
    const handleSsoLogin = () => {
        if (!(ssoConfig === null || ssoConfig === void 0 ? void 0 : ssoConfig.provider))
            return;
        const ssoUrl = `${ssoConfig.provider}/oauth2/authorize?client_id=${encodeURIComponent(API_BASE_URL)}&redirect_uri=${encodeURIComponent(`${API_BASE_URL}/auth/sso/callback`)}`;
        window.location.href = ssoUrl;
    };
    return (_jsxs("div", { className: "login-page", children: [
        _jsx("h1", { children: "Legal AI Tool" }),
        !ssoLoading && (ssoConfig === null || ssoConfig === void 0 ? void 0 : ssoConfig.sso_enabled) && (_jsxs("div", { className: "sso-section", children: [
            _jsxs("button", {
                type: "button",
                className: "sso-button",
                onClick: handleSsoLogin,
                disabled: isLoading,
                "aria-label": `Sign in with SSO${ssoConfig.provider ? ` (${ssoConfig.provider})` : ''}`,
                children: [
                    "Sign in with SSO",
                    ssoConfig.provider && (_jsxs("span", { className: "sso-provider-name", children: [" (", ssoConfig.provider, ")"] }))
                ]
            }),
            _jsx("div", { className: "sso-divider", children: _jsx("span", { children: "or sign in with password" }) })
        ] })),
        _jsxs("form", { onSubmit: handleSubmit, children: [
            _jsxs("div", { children: [_jsx("label", { htmlFor: "email", children: "Email" }), _jsx("input", { id: "email", type: "email", value: email, onChange: (e) => setEmail(e.target.value), required: true, disabled: isLoading })] }),
            _jsxs("div", { children: [_jsx("label", { htmlFor: "password", children: "Password" }), _jsx("input", { id: "password", type: "password", value: password, onChange: (e) => setPassword(e.target.value), required: true, disabled: isLoading })] }),
            error && _jsx("div", { role: "alert", className: "error", children: error }),
            _jsx("button", { type: "submit", disabled: isLoading, children: isLoading ? 'Signing in...' : 'Sign In' })
        ] })
    ] }));
}
