import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SARIP | Agentic Ticketing Dashboard",
  description: "Advanced payment incident resolution with AI agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} antialiased min-h-screen flex`} suppressHydrationWarning>
        {/* Sidebar */}
        <aside className="w-64 border-r border-border p-6 flex flex-col gap-8 glass-morphism hidden md:flex">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center font-bold text-lg shadow-lg shadow-primary/20">
              S
            </div>
            <h1 className="font-bold text-xl tracking-tight">SARIP</h1>
          </div>
          
          <nav className="flex flex-col gap-2">
            <NavItem label="Dashboard" active />
          </nav>

          <div className="mt-auto p-4 rounded-xl bg-secondary/50 border border-border">
            <p className="text-xs text-muted-foreground uppercase font-semibold mb-2">Agent Status</p>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-sm font-medium">System Active</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col min-w-0">
          <header className="h-16 border-b border-border px-8 flex items-center justify-between sticky top-0 bg-background/80 backdrop-blur-md z-10">
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground">/</span>
              <h2 className="font-medium">Overview</h2>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-600 border border-white/10 shadow-inner" />
            </div>
          </header>
          
          <div className="p-8 overflow-y-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}

function NavItem({ label, active = false }: { label: string; active?: boolean }) {
  return (
    <button className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
      active 
        ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
        : "text-muted-foreground hover:bg-secondary hover:text-foreground"
    }`}>
      {label}
    </button>
  );
}
