import { sessionUsername } from "@/lib/auth";
import { getCandidate } from "@/lib/investigations";

const headers = { "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" };

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  try {
    if (!await sessionUsername()) return Response.json({ error: "Your session has expired. Sign in again to view source details." }, { status: 401, headers });
    const { id } = await params;
    const query = new URL(request.url).searchParams;
    const sha = query.get("sha") ?? "";
    const parser = query.get("parser") ?? "";
    const record = query.get("record") ?? "";
    if (id.length > 200 || !sha || sha.length > 128 || !parser || parser.length > 60 || !/^[1-9]\d{0,9}$/.test(record)) {
      return Response.json({ error: "Invalid source record reference." }, { status: 400, headers });
    }
    const candidate = await getCandidate(id);
    const source = candidate.source_records.find((entry) => entry.source_sha256 === sha && entry.parser_version === parser && entry.record_number === Number(record));
    if (!source) return Response.json({ error: "This source record does not belong to the selected candidate." }, { status: 404, headers });
    return Response.json({ source }, { headers });
  } catch (error) {
    if (error instanceof Error && error.message === "Investigation candidate not found") {
      return Response.json({ error: "Candidate not found." }, { status: 404, headers });
    }
    console.error("Comparison source request could not be completed.");
    return Response.json({ error: "Source details could not be loaded. Please retry." }, { status: 503, headers });
  }
}
