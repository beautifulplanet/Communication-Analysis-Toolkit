import { useApi } from '../hooks/useApi';
import StatCard from '../components/StatCard';
import type { SummaryResponse } from '../types';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    PieChart, Pie, Cell, Legend,
} from 'recharts';

interface Props { caseId: string; }

const COLORS = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981', '#ec4899', '#06b6d4'];

function formatDuration(seconds: number): string {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}

const Overview: React.FC<Props> = ({ caseId }) => {
    const { data, loading, error } = useApi<SummaryResponse>(`/cases/${caseId}/summary`);

    if (loading) return <div className="loading-state"><div className="loading-spinner" /> Loading analysis...</div>;
    if (error) return <div className="error-state">Error: {error}</div>;
    if (!data) return null;

    // Pattern chart data
    const patternData = Object.entries(data.pattern_counts_contact).map(([name, count]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        count,
    })).sort((a, b) => b.count - a.count).slice(0, 10);

    // Severity pie
    const severityData = Object.entries(data.severity_breakdown?.contact || {}).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
    }));

    const severityColors: Record<string, string> = {
        Critical: '#ef4444', High: '#f59e0b', Moderate: '#3b82f6', Low: '#10b981',
    };

    return (
        <div>
            <div className="page-header">
                <h1 className="page-header__title">
                    {data.case_name || 'Analysis Overview'}
                </h1>
                <p className="page-header__subtitle">
                    {data.user_label} & {data.contact_label} • {data.period?.start} → {data.period?.end}
                </p>
            </div>

            {/* Stats Row */}
            <div className="stats-grid">
                <StatCard label="Total Days" value={data.total_days} icon="📅" accent="blue"
                    subtitle={`${data.contact_days} with contact`} />
                <StatCard label="Messages Sent" value={data.total_messages_sent} icon="💬" accent="emerald" />
                <StatCard label="Messages Received" value={data.total_messages_received} icon="📩" accent="purple" />
                <StatCard label="Talk Time" value={formatDuration(data.total_talk_seconds)} icon="📞" accent="blue"
                    subtitle={`${data.total_calls} calls total`} />
                <StatCard label={`Hurtful from ${data.contact_label}`} value={data.hurtful_from_contact}
                    icon="⚠️" accent="red" />
                <StatCard label={`Hurtful from ${data.user_label}`} value={data.hurtful_from_user}
                    icon="💬" accent="amber" />
            </div>

            {/* Charts */}
            <div className="charts-grid">
                {/* Top Patterns */}
                {patternData.length > 0 && (
                    <div className="chart-card">
                        <div className="chart-card__title">Top Behavioral Patterns Detected</div>
                        <div className="chart-card__subtitle">From {data.contact_label}'s messages</div>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={patternData} layout="vertical" margin={{ left: 120, right: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                <XAxis type="number" stroke="#64748b" fontSize={12} />
                                <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={110} />
                                <Tooltip
                                    contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                                />
                                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                                    {patternData.map((_, i) => (
                                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Severity Breakdown */}
                {severityData.length > 0 && (
                    <div className="chart-card">
                        <div className="chart-card__title">Hurtful Language Severity</div>
                        <div className="chart-card__subtitle">Distribution from {data.contact_label}</div>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={severityData}
                                    cx="50%" cy="50%"
                                    innerRadius={60} outerRadius={100}
                                    paddingAngle={3}
                                    dataKey="value"
                                >
                                    {severityData.map((entry) => (
                                        <Cell key={entry.name} fill={severityColors[entry.name] || '#64748b'} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                                />
                                <Legend
                                    verticalAlign="bottom"
                                    formatter={(value: string) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Overview;
