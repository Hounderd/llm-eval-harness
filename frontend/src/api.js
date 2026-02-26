const BASE = 'http://localhost:8000'

async function request(path, options = {}) {
    const res = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    })
    if (!res.ok) {
        const err = await res.text()
        throw new Error(err || `HTTP ${res.status}`)
    }
    return res.json()
}

export const api = {
    getStats: () => request('/api/stats'),
    getSuites: () => request('/api/suites'),
    getResults: (suiteId) => request(`/api/results${suiteId ? `?suite_id=${suiteId}` : ''}`),
    getResult: (id) => request(`/api/results/${id}`),
    getProviders: () => request('/api/providers'),
    runSuite: (body) => request('/api/run', { method: 'POST', body: JSON.stringify(body) }),
}
