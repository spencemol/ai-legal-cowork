import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { AuthGuard } from './components/AuthGuard/AuthGuard';
import { LoginPage } from './components/LoginPage/LoginPage';
import { MatterSelector } from './components/MatterSelector/MatterSelector';
import { ConversationList } from './components/ConversationList/ConversationList';
import { ChatWindow } from './components/Chat/ChatWindow';
import { useAuthStore } from './stores/authStore';
import { useChatStore } from './stores/chatStore';
function MainView() {
    const activeMatter = useChatStore((s) => s.activeMatter);
    const logout = useAuthStore((s) => s.logout);
    return (_jsxs("div", { className: "app-layout", children: [_jsxs("aside", { className: "sidebar", children: [_jsxs("div", { className: "sidebar-header", children: [_jsx("h2", { children: "Legal AI Tool" }), _jsx("button", { onClick: logout, type: "button", className: "logout-btn", children: "Sign Out" })] }), _jsx(MatterSelector, {}), activeMatter && _jsx(ConversationList, {})] }), _jsx("main", { className: "main-content", children: _jsx(ChatWindow, {}) })] }));
}
function App() {
    return (_jsx(AuthGuard, { fallback: _jsx(LoginPage, { onLoginSuccess: () => {
                // AuthGuard will automatically show MainView when token is set via Zustand
            } }), children: _jsx(MainView, {}) }));
}
export default App;
