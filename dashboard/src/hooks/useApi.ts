import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';

export function useApi<T>(path: string) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);

        fetch(`${API_BASE}${path}`)
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then((json: T) => {
                if (!cancelled) {
                    setData(json);
                    setLoading(false);
                }
            })
            .catch((err: Error) => {
                if (!cancelled) {
                    setError(err.message);
                    setLoading(false);
                }
            });

        return () => {
            cancelled = true;
        };
    }, [path]);

    return { data, loading, error };
}
