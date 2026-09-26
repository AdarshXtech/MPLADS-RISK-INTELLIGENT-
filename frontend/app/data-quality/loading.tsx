export default function Loading() {
  return (
<<<<<<< HEAD
    <main className="page-content" aria-busy="true" aria-label="Loading Data Quality">
=======
    <main className="page-content" id="main-content" aria-busy="true" aria-label="Loading Data Quality">
>>>>>>> main
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
<<<<<<< HEAD
      <span className="sr-only">Loading current source validation data</span>
=======
      <span className="sr-only">Loading current data-quality information</span>
>>>>>>> main
    </main>
  );
}
