import { jsx as _jsx } from "react/jsx-runtime";
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
describe('ChatInput (Task 5.7)', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });
    it('renders a textarea and send button', async () => {
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: vi.fn(), disabled: false }));
        expect(screen.getByRole('textbox')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });
    it('calls onSend with message text on button click', async () => {
        const onSend = vi.fn();
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: onSend, disabled: false }));
        const textarea = screen.getByRole('textbox');
        await userEvent.type(textarea, 'What is the statute of limitations?');
        fireEvent.click(screen.getByRole('button', { name: /send/i }));
        expect(onSend).toHaveBeenCalledWith('What is the statute of limitations?');
    });
    it('clears input after sending', async () => {
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: vi.fn(), disabled: false }));
        const textarea = screen.getByRole('textbox');
        await userEvent.type(textarea, 'Hello');
        fireEvent.click(screen.getByRole('button', { name: /send/i }));
        await waitFor(() => {
            expect(textarea).toHaveValue('');
        });
    });
    it('does not call onSend if message is empty', async () => {
        const onSend = vi.fn();
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: onSend, disabled: false }));
        fireEvent.click(screen.getByRole('button', { name: /send/i }));
        expect(onSend).not.toHaveBeenCalled();
    });
    it('disables textarea and button when disabled=true', async () => {
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: vi.fn(), disabled: true }));
        expect(screen.getByRole('textbox')).toBeDisabled();
        expect(screen.getByRole('button', { name: /send/i })).toBeDisabled();
    });
    it('sends message on Enter key press (without shift)', async () => {
        const onSend = vi.fn();
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: onSend, disabled: false }));
        const textarea = screen.getByRole('textbox');
        await userEvent.type(textarea, 'Enter test message');
        fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
        expect(onSend).toHaveBeenCalledWith('Enter test message');
    });
    it('does not send on Shift+Enter (allows newline)', async () => {
        const onSend = vi.fn();
        const { ChatInput } = await import('./ChatInput');
        render(_jsx(ChatInput, { onSend: onSend, disabled: false }));
        const textarea = screen.getByRole('textbox');
        await userEvent.type(textarea, 'Line 1');
        fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
        expect(onSend).not.toHaveBeenCalled();
    });
});
