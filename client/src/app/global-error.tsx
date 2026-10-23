'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error('[GLOBAL ERROR]', {
      name: error.name,
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl text-center space-y-6">
          <div className="space-y-2">
            <h1 className="text-xl font-bold tracking-tight text-white">System Error</h1>
            <p className="text-sm text-slate-400">
              A critical error occurred. Please try reloading the application.
            </p>
            {error.digest && (
              <p className="text-xs font-mono text-slate-500 bg-slate-950 py-1 px-2 rounded-md inline-block">
                Reference: {error.digest}
              </p>
            )}
          </div>

          <div className="flex gap-3 justify-center pt-2">
            <button
              onClick={() => reset()}
              className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors"
            >
              Reload Page
            </button>
            <Link
              href="/"
              className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-sm transition-colors border border-slate-700"
            >
              Return Home
            </Link>
          </div>
        </div>
      </body>
    </html>
  );
}
