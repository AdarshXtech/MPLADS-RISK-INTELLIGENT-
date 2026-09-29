export function Brand({ className = "" }: { className?: string }) {
  return (
    <div className={`brand suchak-brand ${className}`}>
      <span className="brand-mark" aria-hidden="true">M</span>
      <span className="brand-copy">
        <strong className="brand-name">MPLADS Risk</strong>
        <span className="brand-context">Intelligence and early warning</span>
      </span>
    </div>
  );
}
