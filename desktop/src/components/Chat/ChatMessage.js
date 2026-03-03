import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function ChatMessage({ message, isStreaming = false, onCitationClick }) {
    const isUser = message.role === 'user';
    return (_jsxs("div", { className: `message ${isUser ? 'message-user' : 'message-assistant'}`, children: [_jsx("div", { className: "message-role", children: isUser ? 'You' : 'Assistant' }), _jsxs("div", { className: "message-content", children: [message.content, isStreaming && _jsx("span", { className: "streaming-cursor", children: "\u258B" })] }), message.citations && message.citations.length > 0 && (_jsx("div", { className: "message-citations", children: message.citations.map((citation, index) => (_jsxs("button", { className: "citation-ref", onClick: () => onCitationClick?.(citation), type: "button", children: ["[", index + 1, "]"] }, citation.chunk_id))) }))] }));
}
