import { redirect } from "next/navigation";

export default function Home() {
  // Mock Auth Guard: Since we're using a mock user in the backend, 
  // we just immediately redirect the root to the dashboard.
  redirect("/dashboard");
}
