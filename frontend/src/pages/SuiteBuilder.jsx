import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import './SuiteBuilder.css'

const EMPTY_CASE = { prompt: '', provider: 'groq', target_model: '', expected_constraints: '' }

export default function SuiteBuilder() {
    const navigate = useNavigate()
    const [providerData, setProviderData] = useState({})
    const [suiteName, setSuiteName] = useState('')
    const [judgeModel, setJudgeModel] = useState('llama-3.3-70b-versatile')
    const [testCases, setTestCases] = useState([{ ...EMPTY_CASE }])
    const [running, setRunning] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        api.getProviders().then(d => setProviderData(d.providers)).catch(console.error)
    }, [])

    function updateCase(i, field, value) {
        setTestCases(prev => {
            const next = [...prev]
            next[i] = { ...next[i], [field]: value }
            // Auto-select first model when provider changes
            if (field === 'provider' && providerData[value]) {
                next[i].target_model = providerData[value][0]
            }
            return next
        })
    }

    function addCase() { setTestCases(prev => [...prev, { ...EMPTY_CASE }]) }
    function removeCase(i) { setTestCases(prev => prev.filter((_, idx) => idx !== i)) }

    async function handleRun() {
        if (!suiteName.trim()) { setError('Please give this suite a name.'); return }
        const invalid = testCases.findIndex(tc => !tc.prompt.trim() || !tc.target_model.trim())
        if (invalid !== -1) { setError(`Test case ${invalid + 1} is missing a prompt or model.`); return }
        setError(null)
        setRunning(true)
        try {
            const payload = {
                name: suiteName.trim(),
                judge_model: judgeModel,
                test_cases: testCases.map(tc => ({
                    prompt: tc.prompt.trim(),
                    provider: tc.provider,
                    target_model: tc.target_model.trim(),
                    expected_constraints: tc.expected_constraints
                        ? (() => { try { return JSON.parse(tc.expected_constraints) } catch { return null } })()
                        : null,
                })),
            }
            await api.runSuite(payload)
            navigate('/')
        } catch (e) {
            setError(e.message)
        } finally {
            setRunning(false)
        }
    }

    return (
        <div className="fade-up">
            <div className="page-header">
                <h1>Run Evaluation Suite</h1>
                <p>Define prompts, pick models, and evaluate them side-by-side</p>
            </div>

            {/* Suite meta */}
            <div className="card suite-meta">
                <div className="field-row">
                    <div className="field">
                        <label>Suite Name</label>
                        <input className="input" placeholder="e.g. Math & Reasoning v2" value={suiteName} onChange={e => setSuiteName(e.target.value)} />
                    </div>
                    <div className="field field-sm">
                        <label>Judge Model</label>
                        <select className="select" value={judgeModel} onChange={e => setJudgeModel(e.target.value)}>
                            {(providerData['groq'] ?? []).map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            {/* Test cases */}
            <div className="cases-section">
                {testCases.map((tc, i) => (
                    <div key={i} className="card test-case-card fade-up" style={{ animationDelay: `${i * 0.06}s` }}>
                        <div className="case-header">
                            <span className="case-num">Case {i + 1}</span>
                            {testCases.length > 1 && (
                                <button className="btn btn-danger btn-sm" onClick={() => removeCase(i)}>Remove</button>
                            )}
                        </div>
                        <div className="case-body">
                            <div className="field full">
                                <label>Prompt</label>
                                <textarea className="input" rows={3} placeholder="What question or task should the model answer?" value={tc.prompt} onChange={e => updateCase(i, 'prompt', e.target.value)} />
                            </div>
                            <div className="field-row">
                                <div className="field">
                                    <label>Provider</label>
                                    <select className="select" value={tc.provider} onChange={e => updateCase(i, 'provider', e.target.value)}>
                                        {Object.keys(providerData).map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                </div>
                                <div className="field">
                                    <label>Model</label>
                                    <select className="select" value={tc.target_model} onChange={e => updateCase(i, 'target_model', e.target.value)}>
                                        {(providerData[tc.provider] ?? []).map(m => <option key={m} value={m}>{m}</option>)}
                                    </select>
                                </div>
                                <div className="field">
                                    <label>Constraints (JSON, optional)</label>
                                    <input className="input" placeholder='{"answer": 42}' value={tc.expected_constraints} onChange={e => updateCase(i, 'expected_constraints', e.target.value)} />
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {error && <div className="error-banner">{error}</div>}

            <div className="actions">
                <button className="btn btn-ghost" onClick={addCase}>+ Add Test Case</button>
                <button className="btn btn-primary" onClick={handleRun} disabled={running}>
                    {running ? <><span className="loading-ring" style={{ width: 16, height: 16, borderWidth: 2 }} /> Running…</> : '▶ Run Suite'}
                </button>
            </div>
        </div>
    )
}
