import PricesTable from './prices-table';

export default function Home() {
  return (
    <main className="container">
      <section className="card">
        <div className="header">
          <div>
            <p className="badge">Live feed · DynamoDB</p>
            <h1 className="title">Crypto Market Pulse</h1>
            <p className="muted">Streaming mini-ticker snapshots from Binance via your AWS data pipe.</p>
          </div>
          <div className="pill">Updated every 10s</div>
        </div>
        <PricesTable />
      </section>
    </main>
  );
}
