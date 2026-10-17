// client/src/app/not-found.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { 
  Home, 
  ArrowLeft, 
  ArrowRight, 
  Sparkles, 
  Crown, 
  BookOpen, 
  MessageSquare
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

export default function NotFound() {
  const quickLinks = [
    {
      label: 'Explore Features',
      href: '/dashboard/automations',
      icon: Sparkles,
      iconColor: 'text-[#6D28D9]',
      iconBg: 'bg-[#EDE9FE]',
    },
    {
      label: 'View Pricing',
      href: '/pricing',
      icon: Crown,
      iconColor: 'text-[#EA580C]',
      iconBg: 'bg-[#FFEDD5]',
    },
    {
      label: 'Help Center',
      href: 'mailto:support@comlina.ai?subject=Comlina%20Help%20Center%20Inquiry',
      icon: BookOpen,
      iconColor: 'text-[#2563EB]',
      iconBg: 'bg-[#DBEAFE]',
    },
    {
      label: 'Contact Support',
      href: '/contact',
      icon: MessageSquare,
      iconColor: 'text-[#7C3AED]',
      iconBg: 'bg-[#F3E8FF]',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-[#FAF9FE] to-[#F3F0FA] text-[#18181B] flex flex-col justify-between selection:bg-[#EDE9FE] selection:text-[#5B21B6]">
      {/* 1. Header / Navbar */}
      <header className="w-full max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
          <BrandLogo variant="horizontal" height={32} />
        </Link>

        {/* Center Nav Links */}
        <nav className="hidden md:flex items-center gap-8 text-[14px] font-medium text-[#71717A]">
          <Link href="/dashboard/automations" className="hover:text-[#18181B] transition-colors">
            Features
          </Link>
          <Link href="/pricing" className="hover:text-[#18181B] transition-colors">
            Pricing
          </Link>
          <Link href="/dashboard/analytics" className="hover:text-[#18181B] transition-colors">
            Resources
          </Link>
          <Link href="/contact" className="hover:text-[#18181B] transition-colors">
            Contact
          </Link>
        </nav>

        {/* Right CTA Actions */}
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="px-4 py-2 rounded-xl text-sm font-medium text-[#3F3F46] hover:text-[#18181B] hover:bg-white/90 border border-transparent hover:border-[#E4E4E7] transition-all"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="flex items-center gap-1.5 px-4.5 py-2 rounded-xl bg-[#5B21B6] hover:bg-[#4C1D95] active:scale-[0.98] text-white text-sm font-semibold shadow-sm hover:shadow transition-all group"
          >
            <span>Get Started</span>
            <ArrowRight size={14} className="text-[#C4B5FD] transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </header>

      {/* 2. Main 404 Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-6 text-center max-w-4xl mx-auto w-full">
        {/* Central 404 Astronaut Illustration */}
        <div className="relative w-full max-w-[680px] mx-auto select-none flex justify-center">
          <Image
            src="/images/404-artwork.png"
            alt="404 Page Not Found"
            width={1024}
            height={315}
            priority
            className="w-full h-auto pointer-events-none select-none"
          />
        </div>

        {/* Text Content */}
        <h1 className="text-3xl md:text-[40px] font-bold tracking-tight text-[#18181B] mt-5 leading-tight">
          <span className="text-[#6D28D9]">Oops! </span>
          This page doesn&apos;t exist.
        </h1>

        <p className="text-sm md:text-base text-[#71717A] max-w-lg mx-auto mt-2.5 leading-relaxed">
          The page you&apos;re looking for might have been moved, deleted, or the link is incorrect.
        </p>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#5B21B6] hover:bg-[#4C1D95] active:scale-[0.98] text-white text-sm font-semibold shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5"
          >
            <Home size={16} />
            <span>Go to Dashboard</span>
          </Link>

          <button
            onClick={() => {
              if (typeof window !== 'undefined') {
                window.history.length > 1 ? window.history.back() : window.location.assign('/dashboard');
              }
            }}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#F4F4F5] hover:bg-[#E4E4E7] active:scale-[0.98] text-[#3F3F46] text-sm font-semibold transition-all cursor-pointer"
          >
            <ArrowLeft size={16} className="text-[#71717A]" />
            <span>Go Back</span>
          </button>
        </div>
      </main>

      {/* 3. Bottom Quick Links Bar */}
      <footer className="w-full max-w-4xl mx-auto px-4 pb-8 pt-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
          {quickLinks.map((item) => {
            const Icon = item.icon;
            const isExternal = item.href.startsWith('mailto:');

            const content = (
              <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-white/90 hover:bg-white border border-[#E4E4E7]/70 hover:border-[#D4D4D8] shadow-xs hover:shadow transition-all group">
                <div className={`w-8 h-8 rounded-xl ${item.iconBg} ${item.iconColor} flex items-center justify-center shrink-0`}>
                  <Icon size={16} />
                </div>
                <div className="flex items-center justify-between flex-1 min-w-0 pr-1">
                  <span className="text-xs font-semibold text-[#18181B] truncate">
                    {item.label}
                  </span>
                  <ArrowRight size={13} className="text-[#A1A1AA] group-hover:text-[#6D28D9] group-hover:translate-x-0.5 transition-all shrink-0 ml-1" />
                </div>
              </div>
            );

            return isExternal ? (
              <a key={item.label} href={item.href} className="block">
                {content}
              </a>
            ) : (
              <Link key={item.label} href={item.href} className="block">
                {content}
              </Link>
            );
          })}
        </div>
      </footer>
    </div>
  );
}
