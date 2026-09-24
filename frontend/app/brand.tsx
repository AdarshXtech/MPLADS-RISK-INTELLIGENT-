import Image from "next/image";

export function Brand({ className = "" }: { className?: string }) {
  return <div className={`brand suchak-brand ${className}`}>
    <span className="brand-logo-crop"><Image src="/brand/suchak-ai.png" alt="Suchak AI" width={1254} height={1254} priority unoptimized /></span>
    <p className="brand-context">MPLADS risk intelligence</p>
  </div>;
}
