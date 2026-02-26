import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import './ResultDetail.css'

function ScoreBar({ rubric, score, reasoning }) {
    const color = score >= 0.75 ? 'good' : score >= 0.4 ? 'mid' : 'bad'
    const pct = Math.round(score * 100)
    return (
        <div className="score-bar-item">
            <div className="score-bar-header">
                <span className="score-bar-label">{rubric.charAt(0).toUpperCase() + rubric.slice(1)}</span>
                <span className={`score-bar-value score-${color}`}>{pct}%</span>
            </div>
            <div className="score-track">
                <div
                    className={`score-fill score-fill-${color}`}
                    style={{ '--target-width': `${pct}%` }}
                />
            </div>
            {reasoning && <p className="score-reasoning">{reasoning}</p>}
        </div>
    )
}

export default function ResultDetail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        api.getResult(id)
            .then(setResult)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [id])

    if (loading) return <div className="center-spinner"><div className="loading-ring" /></div>
    if (error) return <div className="error-page"><h2>Error</h2><p>{error}</p><button className="btn btn-ghost" onClick={() => navigate('/')}>← Back</button></div>

    const { model_name, provider, prompt, response, scores, suite_name, error: evalError } = result

    return (
        <div className="fade-up">
            <button className="back-btn" onClick={() => navigate('/')}>&larr; Back to Dashboard</button>

            <div className="page-header" style={{ marginTop: 16 }}>
                <h1>Evaluation Result</h1>
                <p>Suite: <strong>{suite_name}</strong></p>
            </div>

            <div className="detail-grid">
                {/* Left: prompt + response */}
                <div className="detail-left">
                    <div className="card detail-card">
                        <div className="detail-card-title">Prompt</div>
                        <p className="detail-text">{prompt}</p>
                    </div>

                    <div className="card detail-card">
                        <div className="detail-card-header">
                            <div className="detail-card-title">Response</div>
                            <div className="model-info">
                                <span className={`badge badge-${provider}`}>{provider}</span>
                                <code className="model-tag">{model_name}</code>
                            </div>
                        </div>
                        {evalError ? (
                            <div className="error-banner">{evalError}</div>
                        ) : (
                            <p className="detail-text response-text">{response || '(empty)'}</p>
                        )}
                    </div>
                </div>

                {/* Right: scores */}
                <div className="detail-right">
                    <div className="card detail-card">
                        <div className="detail-card-title">Scores</div>
                        {scores.length === 0 ? (
                            <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No scores available.</p>
                        ) : (
                            <div className="scores-list">
                                {scores.map(s => (
                                    <ScoreBar key={s.rubric_name} rubric={s.rubric_name} score={s.score} reasoning={s.reasoning} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
