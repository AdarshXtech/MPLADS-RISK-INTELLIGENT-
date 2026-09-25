import type { Metadata } from "next";
import { ReviewerDashboard } from "./dashboard";

export const metadata: Metadata = { title: "Command Centre" };

export default function CommandCentrePage() {
  return <ReviewerDashboard view="command-centre" />;
}
