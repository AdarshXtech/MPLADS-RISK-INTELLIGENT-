import Link from "next/link";

export default function NotFound() {
  return <main className="page-content" id="main-content"><section className="error-panel"><h1>Candidate not found</h1><p>This identifier is not present in the current reviewable detector run.</p><Link className="retry-link" href="/investigation-queue">Return to queue</Link></section></main>;
}
