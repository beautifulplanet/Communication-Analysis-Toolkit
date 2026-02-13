import './StatCard.css';

interface StatCardProps {
    label: string;
    value: string | number;
    icon?: string;
    accent?: 'blue' | 'red' | 'amber' | 'emerald' | 'purple';
    subtitle?: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, accent = 'blue', subtitle }) => {
    return (
        <div className={`stat-card stat-card--${accent}`}>
            <div className="stat-card__header">
                {icon && <span className="stat-card__icon">{icon}</span>}
                <span className="stat-card__label">{label}</span>
            </div>
            <div className="stat-card__value">{typeof value === 'number' ? value.toLocaleString() : value}</div>
            {subtitle && <div className="stat-card__subtitle">{subtitle}</div>}
        </div>
    );
};

export default StatCard;
