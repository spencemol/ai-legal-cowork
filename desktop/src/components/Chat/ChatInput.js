import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
export function ChatInput({ onSend, disabled, placeholder = 'Type a message...' }) {
    const [text, setText] = useState('');
    const handleSend = () => {
        const trimmed = text.trim();
        if (!trimmed)
            return;
        onSend(trimmed);
        setText('');
    };
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };
    return (_jsxs("div", { className: "chat-input", children: [_jsx("textarea", { value: text, onChange: (e) => setText(e.target.value), onKeyDown: handleKeyDown, placeholder: placeholder, disabled: disabled, rows: 3 }), _jsx("button", { onClick: handleSend, disabled: disabled, type: "button", children: "Send" })] }));
}
