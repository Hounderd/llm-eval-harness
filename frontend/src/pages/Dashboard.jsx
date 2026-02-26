import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import './Dashboard.css'

function ProviderBadge({ provider }) {
    return <span className={`badge badge-${provider}`}>{provider}</span>
}

function ScorePill({ score }) {
    const color = score >= 0.75 ? 'good' : score >= 0.4 ? 'mid' : 'bad'
    return <span className={`score-pill score-${color}`}>{(score * 100).toFixed(0)}%</span>
}

function StatCard({ label, value, sub }) {
    return (
        <div className="stat-card card fade-up">
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
            {sub && <div className="stat-sub">{sub}</div>}
        </div>
    )
}

export default function Dashboard() {
    const [stats, setStats] = useState(null)
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()

    useEffect(() => {
        Promise.all([api.getStats(), api.getResults()])
            .then(([s, r]) => { setStats(s); setResults(r) })
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [])

    if (loading) {
        return (
            <div className="center-spinner">
                <div className="loading-ring" />
            </div>
        )
    }

    const avgScores = stats?.average_scores ?? {}

    return (
        <div>
            <div className="page-header">
                <h1>Dashboard</h1>
                <p>Overview of your LLM evaluation runs</p>
            </div>

            {/* Stat cards */}
            <div className="stats-grid">
                <StatCard label="Total Evaluations" value={stats?.total_evaluations ?? 0} />
                <StatCard label="Total Suites" value={stats?.total_suites ?? 0} />
                {Object.entries(avgScores).map(([k, v]) => (
                    <StatCard
                        key={k}
                        label={`Avg ${k.charAt(0).toUpperCase() + k.slice(1)}`}
                        value={`${(v * 100).toFixed(1)}%`}
                    />
                ))}
            </div>

            {/* Results table */}
            <div className="card results-card fade-up">
                <div className="results-header">
                    <h2>Recent Evaluations</h2>
                    <button className="btn btn-primary btn-sm" onClick={() => navigate('/run')}>
                        + New Run
                    </button>
                </div>

                {results.length === 0 ? (
                    <div className="empty-state">
                        <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                        <p>No evaluations yet. <button className="link-btn" onClick={() => navigate('/run')}>Run your first suite →</button></p>
                    </div>
                ) : (
                    <div className="table-wrap">
                        <table className="results-table">
                            <thead>
                                <tr>
                                    <th>Prompt</th>
                                    <th>Model</th>
                                    <th>Provider</th>
                                    <th>Correctness</th>
                                    <th>Coherence</th>
                                    <th>Safety</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {results.map((r, i) => {
                                    const scoreMap = Object.fromEntries(r.scores.map(s => [s.rubric_name, s.score]))
                                    return (
                                        <tr key={r.id ?? i} className="result-row" style={{ animationDelay: `${i * 0.04}s` }}>
                                            <td className="prompt-cell" title={r.prompt}>{r.prompt.slice(0, 60)}{r.prompt.length > 60 ? '…' : ''}</td>
                                            <td className="model-cell"><code>{r.model_name}</code></td>
                                            <td><ProviderBadge provider={r.provider} /></td>
                                            <td>{scoreMap.correctness != null ? <ScorePill score={scoreMap.correctness} /> : <span className="text-dim">—</span>}</td>
                                            <td>{scoreMap.coherence != null ? <ScorePill score={scoreMap.coherence} /> : <span className="text-dim">—</span>}</td>
                                            <td>{scoreMap.safety != null ? <ScorePill score={scoreMap.safety} /> : <span className="text-dim">—</span>}</td>
                                            <td><button className="btn btn-ghost btn-sm" onClick={() => navigate(`/results/${r.id}`)}>View</button></td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
