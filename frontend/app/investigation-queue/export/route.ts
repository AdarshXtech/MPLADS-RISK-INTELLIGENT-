import { sessionUsername } from "@/lib/auth";
import { getCandidateCsv } from "@/lib/investigations";

const headers = { "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" };

export async function GET(request: Request) {
  try {
    if (!await sessionUsername()) {
      return Response.json({ error: "Your session has expired. Sign in again to export." }, { status: 401, headers });
    }
    const supplied = new URL(request.url).searchParams;
    const filters = new URLSearchParams();
    for (const key of ["query", "state", "status", "sort"]) {
      const value = supplied.get(key);
      if (value) filters.set(key, value);
    }
    const content = await getCandidateCsv(filters);
    return new Response(content, {
      headers: { ...headers, "Content-Type": "text/csv; charset=utf-8", "Content-Disposition": 'attachment; filename="investigation-queue.csv"' },
    });
  } catch {
    return Response.json({ error: "Export could not be prepared. Try narrower filters or retry when the review service is available." }, { status: 503, headers });
  }
}
