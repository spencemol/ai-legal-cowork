import React from 'react'
import { AuthGuard } from './components/AuthGuard/AuthGuard'
import { LoginPage } from './components/LoginPage/LoginPage'
import { MatterSelector } from './components/MatterSelector/MatterSelector'
import { ConversationList } from './components/ConversationList/ConversationList'
import { ChatWindow } from './components/Chat/ChatWindow'
import { useAuthStore } from './stores/authStore'
import { useChatStore } from './stores/chatStore'

function MainView() {
  const activeMatter = useChatStore((s) => s.activeMatter)
  const logout = useAuthStore((s) => s.logout)

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Legal AI Tool</h2>
          <button onClick={logout} type="button" className="logout-btn">
            Sign Out
          </button>
        </div>
        <MatterSelector />
        {activeMatter && <ConversationList />}
      </aside>
      <main className="main-content">
        <ChatWindow />
      </main>
    </div>
  )
}

function App(): React.JSX.Element {
  return (
    <AuthGuard
      fallback={
        <LoginPage
          onLoginSuccess={() => {
            // AuthGuard will automatically show MainView when token is set via Zustand
          }}
        />
      }
    >
      <MainView />
    </AuthGuard>
  )
}

export default App
