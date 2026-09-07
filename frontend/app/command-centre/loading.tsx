export default function Loading() {
  return (
    <main className="page-content" aria-busy="true" aria-label="Loading command centre">
      <div className="skeleton skeleton-heading" />
      <div className="skeleton skeleton-copy" />
      <div className="loading-grid">
        {[0, 1, 2, 3].map((item) => (
          <div className="skeleton-card" key={item}>
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ))}
      </div>
      <span className="sr-only">Loading current ingestion data</span>
    </main>
  );
}
