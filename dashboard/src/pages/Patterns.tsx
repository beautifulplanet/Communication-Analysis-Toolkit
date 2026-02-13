import { useApi } from '../hooks/useApi';
import type { PatternsResponse } from '../types';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

interface Props { caseId: string; }

const COLORS: Record<string, string> = {
    gaslighting: '#ef4444',
    darvo: '#f97316',
    manipulation: '#f59e0b',
    coercive_control: '#ec4899',
    gottman_four_horsemen: '#8b5cf6',
    stonewalling: '#6366f1',
    contempt: '#dc2626',
    criticism: '#d97706',
    defensiveness: '#0ea5e9',
};

const Patterns: React.FC<Props> = ({ caseId }) => {
    const { data, loading, error } = useApi<PatternsResponse>(`/cases/${caseId}/patterns`);

    if (loading) return <div className="loading-state"><div className="loading-spinner" /> Loading patterns...</div>;
    if (error) return <div className="error-state">Error: {error}</div>;
    if (!data || !data.patterns.length) return (
        <div className="empty-state">
            <div className="empty-state__icon">🔍</div>
            <div className="empty-state__title">No patterns detected</div>
        </div>
    );

    // Bar chart: comparison user vs contact
    const comparisonData = data.patterns.map((p) => ({
        name: p.pattern.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        user: p.total_user,
        contact: p.total_contact,
    })).sort((a, b) => (b.user + b.contact) - (a.user + a.contact));

    // Radar chart: top patterns by contact
    const radarData = comparisonData
        .filter((d) => d.contact > 0)
        .slice(0, 8)
        .map((d) => ({ ...d, fullMark: Math.max(...comparisonData.map((x) => x.contact)) }));

    return (
        <div>
            <div className="page-header">
                <h1 className="page-header__title">Pattern Analysis</h1>
                <p className="page-header__subtitle">
                    {data.patterns.length} distinct patterns • {data.patterns.reduce((s, p) => s + p.total_user + p.total_contact, 0)} total instances
                </p>
            </div>

            {/* Charts */}
            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-card__title">Pattern Comparison</div>
                    <div className="chart-card__subtitle">User vs Contact instances</div>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={comparisonData} layout="vertical" margin={{ left: 120, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis type="number" stroke="#64748b" fontSize={12} />
                            <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={110} />
                            <Tooltip
                                contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                            />
                            <Bar dataKey="contact" name="Contact" fill="#ef4444" radius={[0, 4, 4, 0]} />
                            <Bar dataKey="user" name="User" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {radarData.length >= 3 && (
                    <div className="chart-card">
                        <div className="chart-card__title">Pattern Radar</div>
                        <div className="chart-card__subtitle">Contact behavioral profile</div>
                        <ResponsiveContainer width="100%" height={400}>
                            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                <PolarAngleAxis dataKey="name" stroke="#64748b" fontSize={10} />
                                <PolarRadiusAxis stroke="#64748b" fontSize={10} />
                                <Radar name="Contact" dataKey="contact" stroke="#ef4444" fill="#ef4444" fillOpacity={0.25} />
                                <Radar name="User" dataKey="user" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
                                <Tooltip
                                    contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                                />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>

            {/* Pattern Detail Table */}
            <div className="section-divider">All Detected Patterns</div>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Pattern</th>
                        <th style={{ textAlign: 'right' }}>Contact</th>
                        <th style={{ textAlign: 'right' }}>User</th>
                        <th style={{ textAlign: 'right' }}>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {comparisonData.map((p) => (
                        <tr key={p.name}>
                            <td>
                                <span
                                    style={{
                                        display: 'inline-block',
                                        width: 8, height: 8,
                                        borderRadius: '50%',
                                        background: COLORS[p.name.toLowerCase().replace(/ /g, '_')] || '#64748b',
                                        marginRight: 8,
                                    }}
                                />
                                {p.name}
                            </td>
                            <td style={{ textAlign: 'right', color: 'var(--accent-red)' }}>{p.contact}</td>
                            <td style={{ textAlign: 'right', color: 'var(--accent-blue)' }}>{p.user}</td>
                            <td style={{ textAlign: 'right', fontWeight: 600 }}>{p.contact + p.user}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default Patterns;
