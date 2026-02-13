import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import type { HurtfulResponse, HurtfulItem } from '../types';

interface Props { caseId: string; }

const SEVERITY_ORDER = ['critical', 'high', 'moderate', 'low'];

const Evidence: React.FC<Props> = ({ caseId }) => {
    const { data, loading, error } = useApi<HurtfulResponse>(`/cases/${caseId}/hurtful`);
    const [filter, setFilter] = useState<'all' | 'user' | 'contact'>('all');
    const [severityFilter, setSeverityFilter] = useState<string>('all');
    const [search, setSearch] = useState('');

    if (loading) return <div className="loading-state"><div className="loading-spinner" /> Loading evidence...</div>;
    if (error) return <div className="error-state">Error: {error}</div>;
    if (!data) return null;

    // Combine and filter
    let items: (HurtfulItem & { from: string })[] = [];
    if (filter !== 'contact') items.push(...data.from_user.map((h) => ({ ...h, from: 'User' })));
    if (filter !== 'user') items.push(...data.from_contact.map((h) => ({ ...h, from: 'Contact' })));

    if (severityFilter !== 'all') {
        items = items.filter((h) => h.severity.toLowerCase() === severityFilter.toLowerCase());
    }

    if (search) {
        const q = search.toLowerCase();
        items = items.filter(
            (h) => h.preview.toLowerCase().includes(q) || h.words.some((w) => w.toLowerCase().includes(q))
        );
    }

    // Sort by severity then time
    items.sort((a, b) => {
        const ai = SEVERITY_ORDER.indexOf(a.severity.toLowerCase());
        const bi = SEVERITY_ORDER.indexOf(b.severity.toLowerCase());
        if (ai !== bi) return ai - bi;
        return a.time.localeCompare(b.time);
    });

    const total = data.from_user.length + data.from_contact.length;

    return (
        <div>
            <div className="page-header">
                <h1 className="page-header__title">Evidence Log</h1>
                <p className="page-header__subtitle">
                    {total} hurtful language instances detected
                </p>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
                <div className="case-selector" style={{ margin: 0 }}>
                    {(['all', 'user', 'contact'] as const).map((f) => (
                        <button key={f}
                            className={`case-selector__btn ${filter === f ? 'case-selector__btn--active' : ''}`}
                            onClick={() => setFilter(f)}
                        >
                            {f === 'all' ? 'All' : f === 'user' ? 'User' : 'Contact'}
                        </button>
                    ))}
                </div>
                <div className="case-selector" style={{ margin: 0 }}>
                    <button
                        className={`case-selector__btn ${severityFilter === 'all' ? 'case-selector__btn--active' : ''}`}
                        onClick={() => setSeverityFilter('all')}
                    >All Severity</button>
                    {SEVERITY_ORDER.map((s) => (
                        <button key={s}
                            className={`case-selector__btn ${severityFilter === s ? 'case-selector__btn--active' : ''}`}
                            onClick={() => setSeverityFilter(s)}
                        >
                            <span className={`badge badge--${s}`}>{s}</span>
                        </button>
                    ))}
                </div>
                <input
                    type="text"
                    placeholder="Search messages..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{
                        background: 'var(--card-bg)',
                        border: '1px solid var(--border)',
                        borderRadius: 8,
                        padding: '0.5rem 1rem',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                        fontFamily: 'inherit',
                        outline: 'none',
                        minWidth: 200,
                    }}
                />
            </div>

            {/* Results count */}
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Showing {items.length} of {total} entries
            </p>

            {/* Table */}
            {items.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state__icon">🔎</div>
                    <div className="empty-state__title">No matches</div>
                </div>
            ) : (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Source</th>
                            <th>Severity</th>
                            <th>Time</th>
                            <th>Words</th>
                            <th>Preview</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.slice(0, 200).map((h, i) => (
                            <tr key={i}>
                                <td style={{ fontWeight: 500 }}>{h.from}</td>
                                <td><span className={`badge badge--${h.severity.toLowerCase()}`}>{h.severity}</span></td>
                                <td style={{ whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>{h.time}</td>
                                <td style={{ color: 'var(--accent-red)', fontSize: '0.8rem' }}>
                                    {h.words.join(', ')}
                                </td>
                                <td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.8rem' }}>
                                    {h.preview}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};

export default Evidence;
