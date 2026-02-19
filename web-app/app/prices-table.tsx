"use client";

import useSWR from 'swr';
import { PriceRow, PricesApiResponse } from '../lib/types';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

function formatNumber(value: number, digits = 2) {
  if (Number.isNaN(value)) return '—';
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(digits)}`;
}

function formatPercent(value: number) {
  if (Number.isNaN(value)) return '—';
  if (value === 0) return <span className="muted">0.00%</span>;
  const signClass = value > 0 ? 'price-up' : 'price-down';
  const display = `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  return <span className={signClass}>{display}</span>;
}

function SkeletonRow() {
  return (
    <tr>
      {Array.from({ length: 8 }).map((_, idx) => (
        <td key={idx}>
          <div className="skeleton" style={{ width: idx === 1 ? '160px' : '80px' }} />
        </td>
      ))}
    </tr>
  );
}

export default function PricesTable() {
  const { data, isLoading } = useSWR<PricesApiResponse>('/api/prices', fetcher, {
    refreshInterval: 10_000,
    revalidateOnFocus: false,
  });

  const rows: PriceRow[] = data?.items ?? [];

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Price</th>
            <th>1H</th>
            <th>24H</th>
            <th>7D</th>
            <th>Market Cap</th>
            <th>24H Volume</th>
          </tr>
        </thead>
        <tbody>
          {isLoading && !rows.length && (
            <>
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </>
          )}

          {!isLoading && rows.length === 0 && (
            <tr>
              <td colSpan={8} className="muted" style={{ textAlign: 'center', padding: '18px 0' }}>
                No price snapshots yet. Ensure DynamoDB is receiving mini-ticker writes.
              </td>
            </tr>
          )}

          {rows.map((row, idx) => (
            <tr key={row.symbol}>
              <td>{idx + 1}</td>
              <td>
                <div className="grid-2">
                  <div>
                    <div style={{ fontWeight: 700 }}>{row.assetName}</div>
                    <div className="muted" style={{ fontSize: 13 }}>{row.symbol}</div>
                  </div>
                  <button
                    aria-label="Expand"
                    style={{
                      width: 30,
                      height: 30,
                      borderRadius: 999,
                      border: `1px solid var(--border)`,
                      background: 'rgba(255,255,255,0.03)',
                      color: 'var(--muted)',
                    }}
                  >
                    +
                  </button>
                </div>
              </td>
              <td style={{ fontWeight: 600 }}>{formatNumber(row.price)}</td>
              <td>{formatPercent(row.delta1h)}</td>
              <td>{formatPercent(row.delta24h)}</td>
              <td>{formatPercent(row.delta7d)}</td>
              <td>{formatNumber(row.marketCap, 0)}</td>
              <td>{formatNumber(row.volume24h, 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
