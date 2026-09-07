export default function Loading() {
  return <main className="page-content" id="main-content" aria-busy="true" aria-label="Loading Investigation Queue"><div className="skeleton skeleton-heading" /><div className="skeleton skeleton-copy" /><div className="loading-grid">{Array.from({ length: 4 }, (_, index) => <div className="skeleton-card" key={index}><div className="skeleton" /><div className="skeleton" /></div>)}</div></main>;
}
