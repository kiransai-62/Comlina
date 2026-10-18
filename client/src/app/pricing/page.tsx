// client/src/app/pricing/page.tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  ShieldCheck, 
  Sparkles, 
  CheckCircle, 
  HelpCircle,
  Clock,
  Instagram,
  Lock
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';
import { PlanComparisonMatrix } from '@/components/billing/PlanComparisonMatrix';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { usePlan } from '@/hooks/usePlan';

export default function PricingPage() {
  const { planTier } = usePlan();

  const faqs = [
    {
      q: 'How do the post and DM limits work on the Free plan?',
      a: 'The Free tier gives you up to 10 automated posts total and up to 99 direct messages per post. When you reach 99 DMs on a post, the automation safely pauses for that post to preserve your safety. You can upgrade to Premium (2,500 DMs/post) or Pro (10,000 DMs/post) anytime.',
    },
    {
      q: 'Does Comlina comply with Meta and Instagram platform policies?',
      a: 'Yes. Comlina connects solely through official Meta Graph API endpoints. We strictly adhere to Instagram rate limits, the 7-day comment private reply policy window, and the 24-hour standard messaging window. Your account is never at risk of shadowbanning from unauthorized scrapers.',
    },
    {
      q: 'What payment methods does Razorpay support?',
      a: 'Through our Razorpay gateway, we accept UPI (Google Pay, PhonePe, Paytm, BHIM), Indian & International Credit/Debit Cards (Visa, Mastercard, RuPay, Amex), and Net Banking across all major banks.',
    },
    {
      q: 'Will I lose my existing automations if I upgrade?',
      a: 'Never. When you upgrade, all your existing draft and active automations, contact history, and follower gates are seamlessly preserved and instantly unlocked with higher quotas.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#FBFBFA] text-[#111110]">
      <UpgradeModal />

      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-[#ECECE8]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <BrandLogo variant="mark" height={28} />
            <span className="text-xl font-extrabold tracking-tight text-[#111110]">Comlina</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-[#ECECE8] hover:bg-[#F4F4F0] text-xs font-semibold text-[#111110] transition-colors"
            >
              <ArrowLeft size={14} />
              <span>Back to Dashboard</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-12 space-y-16">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#EAF6EE] text-[#064125] border border-[#C5E7D1]">
            <Sparkles size={13} className="text-[#15803D]" />
            <span>Simple, Transparent Pricing</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-[#111110] tracking-tight">
            Plans built for Indian creators & businesses
          </h1>
          <p className="text-sm sm:text-base text-[#70706B] leading-relaxed">
            Turn passive Instagram scrollers into paying customers. Start free, upgrade to Premium for ₹199/month, or unleash Pro for ₹399/month.
          </p>
        </div>

        {/* Plan Comparison Matrix */}
        <PlanComparisonMatrix />

        {/* Instagram API Policy & Safety Card */}
        <div className="bg-white border border-[#ECECE8] rounded-3xl p-6 sm:p-8 shadow-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#ECECE8] pb-6 mb-6">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-gradient-to-tr from-purple-500 to-pink-500 text-white rounded-2xl shadow-sm">
                <Instagram size={24} />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#111110]">
                  Official Meta Graph API Integration & Compliance
                </h3>
                <p className="text-xs text-[#70706B] mt-0.5">
                  Engineered to respect Instagram messaging policies and protect your account reputation.
                </p>
              </div>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#EAF6EE] text-[#064125]">
              <ShieldCheck size={14} className="text-[#15803D]" />
              <span>100% Policy Compliant</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-[#70706B]">
            <div className="space-y-1.5">
              <div className="font-bold text-[#111110] flex items-center gap-1.5">
                <Clock size={14} className="text-[#0066FF]" />
                <span>7-Day Comment Reply Window</span>
              </div>
              <p>
                Meta allows automated direct private replies to comments within 7 days of the comment creation timestamp.
              </p>
            </div>

            <div className="space-y-1.5">
              <div className="font-bold text-[#111110] flex items-center gap-1.5">
                <Lock size={14} className="text-[#0066FF]" />
                <span>24-Hour Messaging Safety</span>
              </div>
              <p>
                Subsequent follow-up DMs and promotional content comply strictly with the standard 24-hour customer messaging window.
              </p>
            </div>

            <div className="space-y-1.5">
              <div className="font-bold text-[#111110] flex items-center gap-1.5">
                <CheckCircle size={14} className="text-[#15803D]" />
                <span>Zero Account Risk</span>
              </div>
              <p>
                No password sharing, reverse-engineered APIs, or suspicious bots. We use your official Instagram Business connection.
              </p>
            </div>
          </div>
        </div>

        {/* FAQs */}
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="text-center space-y-1">
            <h3 className="text-xl font-bold text-[#111110]">Frequently Asked Questions</h3>
            <p className="text-xs text-[#70706B]">Everything you need to know about plans and entitlements</p>
          </div>

          <div className="divide-y divide-[#ECECE8] bg-white border border-[#ECECE8] rounded-3xl p-6 shadow-xs">
            {faqs.map((faq, idx) => (
              <div key={idx} className="py-4 first:pt-0 last:pb-0 space-y-1.5">
                <h4 className="text-sm font-bold text-[#111110] flex items-center gap-2">
                  <HelpCircle size={15} className="text-[#70706B] shrink-0" />
                  <span>{faq.q}</span>
                </h4>
                <p className="text-xs text-[#70706B] pl-6 leading-relaxed">
                  {faq.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#ECECE8] bg-white py-8 mt-16 text-xs text-[#71717A]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} Comlina. All rights reserved.</p>
          <div className="flex items-center gap-x-6 gap-y-2 flex-wrap justify-center sm:justify-start">
            <Link href="/privacy" className="hover:text-[#111110] transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="hover:text-[#111110] transition-colors">
              Terms of Service
            </Link>
            <Link href="/refund" className="hover:text-[#111110] transition-colors">
              Refund &amp; Cancellation Policy
            </Link>
            <Link href="/contact" className="hover:text-[#111110] transition-colors">
              Contact &amp; Legal
            </Link>
            <Link href="/data-deletion-status" className="hover:text-[#111110] transition-colors">
              Data Deletion Status
            </Link>
            <Link href="/pricing" className="text-[#111110] font-semibold">
              Pricing
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
