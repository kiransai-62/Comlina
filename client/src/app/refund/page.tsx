// client/src/app/refund/page.tsx
import React from 'react';
import Link from 'next/link';
import { 
  CreditCard, 
  ArrowLeft, 
  FileText, 
  ShieldCheck, 
  Mail, 
  Phone,
  Info, 
  RefreshCw, 
  Check, 
  ChevronRight, 
  ExternalLink, 
  Sparkles, 
  Zap, 
  Crown 
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

export const metadata = {
  title: 'Refund & Cancellation Policy | Comlina',
  description: 'Refund, cancellation, and subscription billing policies for Comlina Instagram Automation Platform',
};

const SECTIONS = [
  { id: 'overview', number: '1', title: 'Overview' },
  { id: 'subscription-plans', number: '2', title: 'Subscription Plans' },
  { id: 'subscription-billing', number: '3', title: 'Subscription Billing' },
  { id: 'cancellation', number: '4', title: 'Cancellation' },
  { id: 'refund-requests', number: '5', title: 'Refund Requests' },
  { id: 'non-use', number: '6', title: 'Non-Use of the Service' },
  { id: 'failed-payments', number: '7', title: 'Failed Payments' },
  { id: 'refund-processing', number: '8', title: 'Refund Processing' },
  { id: 'third-party-interruptions', number: '9', title: 'Third-Party Disruptions' },
  { id: 'how-to-request', number: '10', title: 'How to Request or Cancel' },
  { id: 'policy-changes', number: '11', title: 'Policy Changes' },
  { id: 'contact-information', number: '12', title: 'Contact Information' },
];

export default function RefundPolicyPage() {
  return (
    <div className="min-h-screen bg-[#FAF9F7] text-[#18181B] selection:bg-[#EDE9FE] selection:text-[#5B21B6]">
      {/* 1. Header / Navbar */}
      <header className="border-b border-[#E4E4E7]/80 bg-white/95 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
            <BrandLogo variant="horizontal" height={30} />
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#71717A] hover:text-[#18181B] px-3 py-1.5 rounded-lg hover:bg-[#F4F4F5] transition-colors"
            >
              <ArrowLeft size={14} />
              <span>Back to Home</span>
            </Link>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#5B21B6] hover:bg-[#4C1D95] text-white px-3.5 py-1.5 rounded-lg shadow-2xs transition-colors"
            >
              <span>View Pricing &amp; Plans</span>
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <div className="bg-white border-b border-[#E4E4E7]/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#EDE9FE] text-[#6D28D9] rounded-full text-xs font-semibold mb-3">
            <CreditCard size={14} />
            <span>Billing &amp; Subscriptions Policy</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#18181B]">
            Refund &amp; Cancellation Policy
          </h1>
          <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs font-medium text-[#71717A] mt-3">
            <span><strong>Effective Date:</strong> October 17, 2026</span>
            <span className="text-[#D4D4D8]">•</span>
            <span><strong>Last Updated:</strong> October 17, 2026</span>
            <span className="text-[#D4D4D8]">•</span>
            <span className="text-[#15803D] flex items-center gap-1 font-semibold">
              <ShieldCheck size={14} /> Razorpay &amp; Consumer Rights Compliant
            </span>
          </div>
        </div>
      </div>

      {/* 3. Main Body with Sticky Sidebar TOC */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Table of Contents Sticky Sidebar */}
          <aside className="hidden lg:block lg:col-span-4 sticky top-24">
            <div className="bg-white border border-[#E4E4E7] rounded-2xl p-5 shadow-2xs">
              <div className="flex items-center gap-2 pb-3 mb-3 border-b border-[#F4F4F5]">
                <FileText size={16} className="text-[#6D28D9]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B]">
                  Table of Contents
                </h3>
              </div>
              <nav className="space-y-1 text-xs">
                {SECTIONS.map((sec) => (
                  <a
                    key={sec.id}
                    href={`#${sec.id}`}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-lg text-[#52525B] hover:text-[#5B21B6] hover:bg-[#F5F3FF] transition-colors group"
                  >
                    <span className="truncate pr-2">
                      <span className="font-semibold text-[#A1A1AA] group-hover:text-[#6D28D9] mr-1.5">
                        {sec.number}.
                      </span>
                      {sec.title}
                    </span>
                    <ChevronRight size={12} className="text-[#D4D4D8] group-hover:text-[#6D28D9] shrink-0" />
                  </a>
                ))}
              </nav>

              <div className="mt-5 pt-4 border-t border-[#F4F4F5] bg-[#FAF5FF] -mx-5 -mb-5 p-4 rounded-b-2xl">
                <div className="flex items-start gap-2.5">
                  <Info size={15} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold text-[#5B21B6]">Need a Refund or Cancellation?</h4>
                    <p className="text-[11px] text-[#71717A] mt-0.5">
                      Contact our support desk directly with your payment reference.
                    </p>
                    <a
                      href="mailto:support@comlina.ai?subject=Refund%20Request%20or%20Subscription%20Cancellation"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#6D28D9] hover:underline mt-1.5"
                    >
                      <span>Email Support Desk</span>
                      <ExternalLink size={11} />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Policy Content Area */}
          <main className="lg:col-span-8 space-y-6">
            {/* Section 1 */}
            <section id="overview" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  1
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Overview</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Comlina offers subscription-based software features for supported Instagram automations and related workflows.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                This policy explains how subscription cancellation, refund requests, payment failures, and subscription access are handled.
              </p>
            </section>

            {/* Section 2 */}
            <section id="subscription-plans" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  2
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Subscription Plans</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">
                Comlina offers three subscription tiers:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-4 rounded-xl border border-[#E4E4E7] bg-[#FAFAFA]">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#52525B] uppercase tracking-wider mb-1">
                    <Sparkles size={13} className="text-[#71717A]" />
                    Free
                  </div>
                  <div className="text-xl font-extrabold text-[#18181B]">₹0</div>
                  <p className="text-[11px] text-[#71717A] mt-1">10 lifetime posts, 99 DMs/post, basic triggers.</p>
                </div>

                <div className="p-4 rounded-xl border border-[#15803D]/30 bg-[#F0FDF4]">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#15803D] uppercase tracking-wider mb-1">
                    <Zap size={13} />
                    Premium
                  </div>
                  <div className="text-xl font-extrabold text-[#15803D]">₹199 <span className="text-xs font-normal text-[#52525B]">/ month</span></div>
                  <p className="text-[11px] text-[#52525B] mt-1">100 posts, 2,500 DMs/post, teaser reply, ask to follow.</p>
                </div>

                <div className="p-4 rounded-xl border border-[#6D28D9]/30 bg-[#FAF5FF]">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#6D28D9] uppercase tracking-wider mb-1">
                    <Crown size={13} />
                    Pro
                  </div>
                  <div className="text-xl font-extrabold text-[#6D28D9]">₹399 <span className="text-xs font-normal text-[#52525B]">/ month</span></div>
                  <p className="text-[11px] text-[#52525B] mt-1">Unlimited posts, 10,000 DMs/post, AI Smart Assistant, Live comment.</p>
                </div>
              </div>

              <p className="text-xs text-[#71717A] leading-relaxed pt-1">
                Prices, billing periods, taxes, and available features will be displayed on the pricing or checkout page before purchase. The applicable checkout terms govern the actual purchase.
              </p>
            </section>

            {/* Section 3 */}
            <section id="subscription-billing" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  3
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Subscription Billing</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Paid subscriptions are billed according to the plan and billing frequency selected during checkout.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Where recurring billing is enabled, renewal payments may be collected through the configured payment provider (such as Razorpay), subject to the applicable payment authorization and provider rules.
              </p>
              <div className="p-3.5 rounded-xl bg-[#FAF9FE] border border-[#E9E4F5] text-xs text-[#4C1D95]">
                Users should review the plan, price, renewal frequency, and applicable taxes before confirming payment.
              </div>
            </section>

            {/* Section 4 */}
            <section id="cancellation" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  4
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Cancellation</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Users may request cancellation through the billing settings in the dashboard, if available, or by contacting Comlina support.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Where the subscription renews automatically, cancellation should be completed before the next renewal charge to avoid that charge, subject to the payment provider&apos;s processing rules.
              </p>
              <div className="border border-[#F4F4F5] bg-[#FAFAFA] rounded-xl p-4 space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B]">After cancellation:</h3>
                <ul className="list-disc pl-5 space-y-1.5 text-xs text-[#52525B]">
                  <li>Future renewals should stop once cancellation is successfully processed.</li>
                  <li>Access may continue until the end of the already-paid billing period, depending on the plan terms.</li>
                  <li>Previously incurred payment obligations remain payable where legally applicable.</li>
                  <li>Cancellation does not automatically guarantee a refund for a past payment.</li>
                </ul>
              </div>
              <p className="text-xs text-[#71717A] italic">
                We will communicate the applicable cancellation status and access period where available.
              </p>
            </section>

            {/* Section 5 */}
            <section id="refund-requests" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  5
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Refund Requests</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Because Comlina is a digital software service, refund eligibility depends on the circumstances, the displayed purchase terms, and applicable law.
              </p>
              <p className="text-sm text-[#3F3F46]">
                You may contact support to request a refund review in circumstances such as:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#52525B]">
                {[
                  'Duplicate charges.',
                  'A payment collected after a successfully processed cancellation.',
                  'An incorrect amount charged.',
                  'A payment that succeeded but did not result in the purchased entitlement being activated.',
                  'Unauthorized transactions or suspected payment fraud.',
                  'Other circumstances where a refund is required by applicable law or the purchase terms.',
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-2.5 rounded-lg bg-[#FAF9F7] border border-[#F4F4F5]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#6D28D9] shrink-0 mt-1.5"></span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[#71717A] pt-1">
                Please explain the issue and provide the transaction reference. We may request reasonable information needed to investigate the payment.
              </p>
            </section>

            {/* Section 6 */}
            <section id="non-use" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  6
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Non-Use of the Service</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Not using Comlina during a billing period does not, by itself, establish refund eligibility.
              </p>
              <p className="text-xs text-[#71717A] leading-relaxed">
                However, this section does not limit any refund, cancellation, or consumer right that applies under the law or the specific purchase terms.
              </p>
            </section>

            {/* Section 7 */}
            <section id="failed-payments" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  7
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Failed Payments</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">If a payment fails:</p>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-[#52525B]">
                <li>The subscription may remain unpaid or become past due.</li>
                <li>Paid features may remain locked or be restricted according to the subscription terms.</li>
                <li>Users may be asked to retry payment or use another supported payment method.</li>
                <li>We will not treat a failed payment attempt as a successful purchase.</li>
              </ul>
              <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 leading-relaxed">
                If the payment provider reports a successful payment but Comlina does not activate the purchased plan, contact support immediately so we can investigate and reconcile the transaction.
              </div>
            </section>

            {/* Section 8 */}
            <section id="refund-processing" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  8
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Refund Processing</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Approved refunds will be initiated through the applicable payment provider or payment method (such as Razorpay back to the original source method), where supported.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                The time required for the refund to appear in the customer&apos;s account may depend on the provider, bank, payment method, and applicable processing rules (typically 5 to 7 business days for UPI/card refunds).
              </p>
              <p className="text-xs text-[#71717A] italic">
                We will communicate the outcome of the refund request where reasonably possible.
              </p>
            </section>

            {/* Section 9 */}
            <section id="third-party-interruptions" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  9
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Instagram and Third-Party Service Interruptions</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Comlina may rely on Instagram, Meta APIs, and other third-party services. Availability may be affected by platform outages, permission changes, API restrictions, or other circumstances outside our control.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                These circumstances do not automatically determine refund eligibility. Requests will be assessed under the applicable purchase terms and law.
              </p>
            </section>

            {/* Section 10 */}
            <section id="how-to-request" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  10
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">How to Request a Refund or Cancel</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">Please contact our billing support desk:</p>
              <div className="p-4 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-2 text-xs">
                <div>
                  <span className="font-semibold text-[#18181B]">Email: </span>
                  <a href="mailto:support@comlina.ai" className="text-[#6D28D9] font-semibold hover:underline">
                    support@comlina.ai
                  </a>
                  <span className="text-[#D4D4D8] mx-2">•</span>
                  <a href="mailto:billing@comlina.com" className="text-[#6D28D9] font-semibold hover:underline">
                    billing@comlina.com
                  </a>
                </div>
                <div>
                  <span className="font-semibold text-[#18181B]">Subject: </span>
                  <span className="font-mono bg-white px-2 py-0.5 rounded border border-[#ECECE8] text-[#52525B]">
                    Refund Request or Subscription Cancellation
                  </span>
                </div>
                <div className="pt-2">
                  <span className="font-semibold text-[#18181B] block mb-1">Please include in your request:</span>
                  <ul className="list-disc pl-5 space-y-1 text-[#52525B]">
                    <li>The email address associated with your Comlina account.</li>
                    <li>The payment, order reference, or Razorpay payment ID, if available.</li>
                    <li>The plan purchased (Premium ₹199 or Pro ₹399).</li>
                    <li>A brief description of the issue.</li>
                    <li>Relevant dates or supporting screenshots/statements.</li>
                  </ul>
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-red-50/70 border border-red-200/60 text-xs text-red-900 leading-relaxed font-medium">
                Security Notice: Never send your password, complete card details, CVV, UPI PIN, or authentication OTPs in support requests.
              </div>
            </section>

            {/* Section 11 */}
            <section id="policy-changes" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  11
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Policy Changes</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                We may update this policy when our subscription model, payment arrangements, or legal obligations change. Updated terms will be published on this page.
              </p>
            </section>

            {/* Section 12 */}
            <section id="contact-information" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  12
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Contact Information</h2>
              </div>
              <div className="space-y-3 p-4 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] text-xs">
                <div>
                  <span className="font-semibold text-[#18181B] block">Operator / Legal Name:</span>
                  <span className="font-semibold text-[#18181B]">Challala Kiran Sai (Comlina)</span>
                </div>
                <div>
                  <span className="font-semibold text-[#18181B] block">Official Email:</span>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 mt-0.5">
                    <a href="mailto:kiransai.challala@gmail.com" className="text-[#6D28D9] hover:underline font-semibold">
                      kiransai.challala@gmail.com
                    </a>
                    <span className="text-[#D4D4D8]">•</span>
                    <a href="mailto:support@comlina.ai" className="text-[#6D28D9] hover:underline font-semibold">
                      support@comlina.ai
                    </a>
                    <span className="text-[#D4D4D8]">•</span>
                    <a href="mailto:billing@comlina.com" className="text-[#6D28D9] hover:underline font-semibold">
                      billing@comlina.com
                    </a>
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-[#18181B] block">Telephone / Contact:</span>
                  <a href="tel:+919014736476" className="text-[#6D28D9] hover:underline font-semibold">
                    +91 9014736476
                  </a>
                </div>
                <div>
                  <span className="font-semibold text-[#18181B] block">Business Address:</span>
                  <span className="text-[#52525B]">HSR Layout, Bengaluru, Karnataka, India 560102</span>
                </div>
              </div>
              <div className="p-3.5 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-xs text-[#15803D] font-medium">
                Nothing in this policy excludes or limits consumer rights that cannot lawfully be excluded or limited under applicable law.
              </div>
            </section>
          </main>
        </div>
      </div>

      {/* 4. Footer */}
      <footer className="border-t border-[#E4E4E7]/80 bg-white py-8 mt-12 text-xs text-[#71717A]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} Comlina. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <Link href="/privacy" className="hover:text-[#18181B] transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="hover:text-[#18181B] transition-colors">
              Terms of Service
            </Link>
            <Link href="/refund" className="text-[#18181B] font-semibold">
              Refund &amp; Cancellation Policy
            </Link>
            <Link href="/contact" className="hover:text-[#18181B] transition-colors">
              Contact &amp; Legal
            </Link>
            <Link href="/data-deletion-status" className="hover:text-[#18181B] transition-colors">
              Data Deletion Status
            </Link>
            <Link href="/pricing" className="hover:text-[#18181B] transition-colors">
              Pricing
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
