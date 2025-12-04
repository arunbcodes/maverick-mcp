import Link from 'next/link';
import { TrendingUp } from 'lucide-react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
      {/* Header */}
      <header className="p-6">
        <Link href="/" className="inline-flex items-center space-x-2">
          <TrendingUp className="h-8 w-8 text-emerald-400" />
          <span className="text-xl font-bold text-white">Maverick</span>
        </Link>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center p-4">
        {children}
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-sm text-slate-500">
        <p>© 2024 Maverick. For educational purposes only.</p>
      </footer>
    </div>
  );
}

