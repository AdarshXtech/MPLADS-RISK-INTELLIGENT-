import type { Metadata } from "next";
import { ReviewerDashboard } from "../command-centre/dashboard";

export const metadata: Metadata = { title: "Data Quality" };

export default function DataQualityPage() {
  return <ReviewerDashboard view="data-quality" />;
}
