import { useApi } from '../hooks/useApi';
import type { TimelineResponse } from '../types';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
    BarChart, Bar, Cell,
} from 'recharts';

interface Props { caseId: string; }

const Timeline: React.FC<Props> = ({ caseId }) => {
    const { data, loading, error } = useApi<TimelineResponse>(`/cases/${caseId}/timeline`);

    if (loading) return <div className="loading-state"><div className="loading-spinner" /> Loading timeline...</div>;
    if (error) return <div className="error-state">Error: {error}</div>;
    if (!data || !data.days.length) return (
        <div className="empty-state">
            <div className="empty-state__icon">📅</div>
            <div className="empty-state__title">No timeline data</div>
        </div>
    );

    // Prepare chart data
    const chartData = data.days.map((d) => ({
        date: d.date,
        sent: d.messages.sent,
        received: d.messages.received,
        hurtful: d.hurtful_from_contact.length + d.hurtful_from_user.length,
        patterns: d.patterns_from_contact.length + d.patterns_from_user.length,
    }));

    // Aggregate by month for the bar chart
    const monthlyData: Record<string, { month: string; messages: number; patterns: number }> = {};
    chartData.forEach((d) => {
        const month = d.date.substring(0, 7); // YYYY-MM
        if (!monthlyData[month]) monthlyData[month] = { month, messages: 0, patterns: 0 };
        monthlyData[month].messages += d.sent + d.received;
        monthlyData[month].patterns += d.patterns;
    });
    const monthlyArr = Object.values(monthlyData);

    return (
        <div>
            <div className="page-header">
                <h1 className="page-header__title">Timeline</h1>
                <p className="page-header__subtitle">
                    {data.days.length} days tracked • {data.gaps.length} communication gaps
                </p>
            </div>

            {/* Daily Message Volume */}
            <div className="chart-card" style={{ marginBottom: '1.5rem' }}>
                <div className="chart-card__title">Daily Message Volume</div>
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                        <defs>
                            <linearGradient id="gradSent" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="gradRecv" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                        <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickFormatter={(v: string) => v.substring(5)} />
                        <YAxis stroke="#64748b" fontSize={12} />
                        <Tooltip
                            contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                        />
                        <Area type="monotone" dataKey="sent" name="Sent" stroke="#3b82f6" fill="url(#gradSent)" strokeWidth={2} />
                        <Area type="monotone" dataKey="received" name="Received" stroke="#8b5cf6" fill="url(#gradRecv)" strokeWidth={2} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Monthly Breakdown */}
            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-card__title">Monthly Message Volume</div>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={monthlyArr}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip
                                contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                            />
                            <Bar dataKey="messages" name="Messages" radius={[4, 4, 0, 0]}>
                                {monthlyArr.map((_, i) => (
                                    <Cell key={i} fill={i % 2 === 0 ? '#3b82f6' : '#60a5fa'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card">
                    <div className="chart-card__title">Monthly Pattern Detections</div>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={monthlyArr}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip
                                contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3b', borderRadius: 8, fontSize: 13 }}
                            />
                            <Bar dataKey="patterns" name="Patterns" radius={[4, 4, 0, 0]}>
                                {monthlyArr.map((_, i) => (
                                    <Cell key={i} fill={i % 2 === 0 ? '#ef4444' : '#f87171'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Communication Gaps */}
            {data.gaps.length > 0 && (
                <>
                    <div className="section-divider">Communication Gaps</div>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Start</th>
                                <th>End</th>
                                <th>Duration</th>
                                <th>Context</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.gaps.map((g, i) => (
                                <tr key={i}>
                                    <td>{g.start}</td>
                                    <td>{g.end}</td>
                                    <td>{g.days} day{g.days !== 1 ? 's' : ''}</td>
                                    <td style={{ color: 'var(--text-muted)' }}>{g.reason || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}
        </div>
    );
};

export default Timeline;
