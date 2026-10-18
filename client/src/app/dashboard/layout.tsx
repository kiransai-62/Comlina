'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopHeader } from '@/components/layout/TopHeader';
import { BottomNav } from '@/components/layout/BottomNav';
import { AuthGuard } from '@/components/AuthGuard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
    },
  },
});

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <QueryClientProvider client={queryClient}>
        <div className="flex h-screen overflow-hidden bg-[#FBFBFA]">
          {/* Sidebar: persistent on Desktop, slide-over drawer on Tablet & Mobile */}
          <Sidebar />

          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
            <TopHeader />
            <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 pb-20 md:pb-6 lg:pb-8">
              {children}
            </main>
          </div>

          {/* Bottom Navigation for Mobile (< 768px) */}
          <BottomNav />
        </div>
      </QueryClientProvider>
    </AuthGuard>
  );
}
