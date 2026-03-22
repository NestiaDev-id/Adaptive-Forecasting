import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";

function App() {
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
