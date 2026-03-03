import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../../stores/authStore';
const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';
export function DocumentViewer({ citation, onClose }) {
    const [document, setDocument] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const token = useAuthStore((s) => s.token);
    const highlightRef = useRef(null);
    useEffect(() => {
        if (!citation) {
            setDocument(null);
            setError(null);
            return;
        }
        const fetchDocument = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const headers = { 'Content-Type': 'application/json' };
                if (token)
                    headers['Authorization'] = `Bearer ${token}`;
                const response = await fetch(`${API_BASE_URL}/documents/${citation.doc_id}`, { headers });
                if (!response.ok) {
                    throw new Error('Failed to load document');
                }
                const body = await response.json();
                setDocument(body.data);
            }
            catch (err) {
                setError(err instanceof Error ? err.message : 'Error loading document');
            }
            finally {
                setIsLoading(false);
            }
        };
        void fetchDocument();
    }, [citation, token]);
    // Scroll highlighted chunk into view after render (guarded for jsdom compatibility)
    useEffect(() => {
        if (highlightRef.current && typeof highlightRef.current.scrollIntoView === 'function') {
            highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [document]);
    if (!citation)
        return null;
    if (isLoading) {
        return (_jsxs("div", { className: "document-viewer", children: [_jsx("div", { className: "document-viewer-header", children: _jsx("button", { onClick: onClose, type: "button", children: "Close" }) }), _jsx("div", { children: "Loading document..." })] }));
    }
    if (error) {
        return (_jsxs("div", { className: "document-viewer", children: [_jsx("div", { className: "document-viewer-header", children: _jsx("button", { onClick: onClose, type: "button", children: "Close" }) }), _jsxs("div", { className: "error", children: ["Error: ", error] })] }));
    }
    if (!document)
        return null;
    // Render content with highlighted snippet
    const renderContent = () => {
        if (!citation.text_snippet || !document.content.includes(citation.text_snippet)) {
            return _jsx("pre", { className: "document-content", children: document.content });
        }
        const snippetIndex = document.content.indexOf(citation.text_snippet);
        const before = document.content.slice(0, snippetIndex);
        const snippet = document.content.slice(snippetIndex, snippetIndex + citation.text_snippet.length);
        const after = document.content.slice(snippetIndex + citation.text_snippet.length);
        return (_jsxs("pre", { className: "document-content", children: [before, _jsx("span", { className: "highlighted-chunk", ref: highlightRef, children: snippet }), after] }));
    };
    return (_jsxs("div", { className: "document-viewer", children: [_jsxs("div", { className: "document-viewer-header", children: [_jsx("h3", { children: document.title }), _jsx("button", { onClick: onClose, type: "button", children: "Close" })] }), _jsx("div", { className: "document-viewer-body", children: renderContent() })] }));
}
