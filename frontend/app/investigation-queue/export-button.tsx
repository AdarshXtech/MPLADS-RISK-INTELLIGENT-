"use client";

import { useState } from "react";

export function ExportButton({ filters }: { filters: string }) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [failed, setFailed] = useState(false);

  async function download() {
    setPending(true);
    setMessage("");
    setFailed(false);
    try {
      const response = await fetch(`/investigation-queue/export?${filters}`, { cache: "no-store", signal: AbortSignal.timeout(15000) });
      if (!response.ok) {
        const problem = await response.json();
        throw new Error(problem.error ?? "Export failed. Please retry.");
      }
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = "investigation-queue.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage("CSV download started for all matching candidates.");
    } catch (error) {
      setFailed(true);
      setMessage(error instanceof Error ? error.message : "Export failed. Please retry.");
    } finally {
      setPending(false);
    }
  }

  return <div className="queue-export">
    <button type="button" onClick={download} disabled={pending}>{pending ? "Preparing CSV..." : "Export filtered CSV"}</button>
    {message && <p role={failed ? "alert" : "status"}>{message}</p>}
  </div>;
}
