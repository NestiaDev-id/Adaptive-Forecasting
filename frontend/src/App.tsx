import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { toast } from "sonner";
import { Sidebar } from "@/components/Sidebar";
import { BASE_URL } from "@/lib/baseUrl";

function App() {
  useEffect(() => {
    if (import.meta.env.PROD && !BASE_URL) {
      toast.warning("Backend URL not configured", {
        description:
          "VITE_API_URL is not set. API calls will fail until you configure the " +
          "backend URL in your hosting provider's environment variables and redeploy.",
        duration: Infinity,
        closeButton: true,
      });
    }
  }, []);

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 ml-64">
        <Outlet />
      </main>
    </div>
  );
}

export default App;
