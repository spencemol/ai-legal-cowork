export function createSSEClient(url, body, token) {
    let tokenCallback = null;
    let citationsCallback = null;
    let errorCallback = null;
    let abortController = null;
    function parseSSELine(buffer) {
        const lines = buffer.split('\n');
        let currentEvent = '';
        let currentData = '';
        for (const line of lines) {
            if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
            }
            else if (line.startsWith('data: ')) {
                currentData = line.slice(6).trim();
            }
            else if (line === '' && currentEvent && currentData) {
                try {
                    if (currentEvent === 'token') {
                        const parsed = JSON.parse(currentData);
                        tokenCallback?.(parsed.token);
                    }
                    else if (currentEvent === 'citations') {
                        const parsed = JSON.parse(currentData);
                        citationsCallback?.(parsed.citations);
                    }
                }
                catch {
                    // Ignore parse errors for individual events
                }
                currentEvent = '';
                currentData = '';
            }
        }
    }
    return {
        onToken(cb) {
            tokenCallback = cb;
        },
        onCitations(cb) {
            citationsCallback = cb;
        },
        onError(cb) {
            errorCallback = cb;
        },
        async connect() {
            abortController = new AbortController();
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                        Accept: 'text/event-stream',
                    },
                    body: JSON.stringify(body),
                    signal: abortController.signal,
                });
                if (!response.ok || !response.body) {
                    throw new Error(`SSE connection failed: ${response.status}`);
                }
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                while (true) {
                    const { done, value } = await reader.read();
                    if (done)
                        break;
                    const chunk = decoder.decode(value, { stream: true });
                    parseSSELine(chunk);
                }
            }
            catch (err) {
                if (err instanceof Error && err.name === 'AbortError')
                    return;
                errorCallback?.(err instanceof Error ? err : new Error(String(err)));
            }
        },
        disconnect() {
            abortController?.abort();
        },
    };
}
