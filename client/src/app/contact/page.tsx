// client/src/app/contact/page.tsx
import React from 'react';
import Link from 'next/link';
import { 
  Mail, 
  Phone,
  Clock, 
  ShieldCheck, 
  FileText, 
  CreditCard, 
  Lock, 
  Globe, 
  ChevronRight, 
  ArrowRight, 
  ArrowLeft, 
  ExternalLink, 
  Shield, 
  Instagram, 
  Check 
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

export const metadata = {
  title: 'Contact & Legal Information | Comlina',
  description: 'Official contact details, customer support hours, billing enquiries, privacy requests, and legal notices for Comlina',
};

const SECTIONS = [
  { id: 'platform-information', number: '1', title: 'Platform Information' },
  { id: 'customer-support', number: '2', title: 'Customer Support' },
  { id: 'billing-and-payments', number: '3', title: 'Billing and Payments' },
  { id: 'privacy-requests', number: '4', title: 'Privacy Requests' },
  { id: 'legal-notices', number: '5', title: 'Legal Notices' },
  { id: 'policies-and-documents', number: '6', title: 'Policies and Documents' },
  { id: 'third-party-platforms', number: '7', title: 'Third-Party Platforms' },
  { id: 'accuracy-of-information', number: '8', title: 'Accuracy of Information' },
];

export default function ContactLegalPage() {
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
              href="/dashboard"
              className="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#5B21B6] hover:bg-[#4C1D95] text-white px-3.5 py-1.5 rounded-lg shadow-2xs transition-colors"
            >
              <span>Go to Dashboard</span>
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <div className="bg-white border-b border-[#E4E4E7]/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#EDE9FE] text-[#6D28D9] rounded-full text-xs font-semibold mb-3">
            <Shield size={14} />
            <span>Corporate Governance &amp; Directory</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#18181B]">
            Contact &amp; Legal Information
          </h1>
          <p className="text-sm text-[#71717A] max-w-2xl mt-2 leading-relaxed">
            Welcome to Comlina. This page provides contact information for customer support, billing enquiries, privacy requests, and legal notices.
          </p>
          <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs font-medium text-[#71717A] mt-4">
            <span><strong>Last Updated:</strong> October 17, 2026</span>
            <span className="text-[#D4D4D8]">•</span>
            <span className="text-[#15803D] flex items-center gap-1 font-semibold">
              <ShieldCheck size={14} /> Verified Legal Operator &amp; Razorpay Registered
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
                  <Mail size={15} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold text-[#5B21B6]">Direct Contacts</h4>
                    <div className="space-y-1 mt-1 text-[11px]">
                      <div>
                        <span className="text-[#71717A]">Official: </span>
                        <a href="mailto:kiransai.challala@gmail.com" className="font-semibold text-[#6D28D9] hover:underline">
                          kiransai.challala@gmail.com
                        </a>
                      </div>
                      <div>
                        <span className="text-[#71717A]">Phone: </span>
                        <a href="tel:+919014736476" className="font-semibold text-[#6D28D9] hover:underline">
                          +91 9014736476
                        </a>
                      </div>
                      <div>
                        <span className="text-[#71717A]">Support: </span>
                        <a href="mailto:support@comlina.ai" className="font-semibold text-[#6D28D9] hover:underline">
                          support@comlina.ai
                        </a>
                      </div>
                      <div>
                        <span className="text-[#71717A]">Billing: </span>
                        <a href="mailto:billing@comlina.com" className="font-semibold text-[#6D28D9] hover:underline">
                          billing@comlina.com
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Directory Content Area */}
          <main className="lg:col-span-8 space-y-6">
            {/* Section 1 */}
            <section id="platform-information" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  1
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Platform Information</h2>
              </div>
              <div className="divide-y divide-[#F4F4F5] border border-[#F4F4F5] bg-[#FAFAFA] rounded-xl text-xs">
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Product Name</span>
                  <span className="font-bold text-[#18181B]">Comlina</span>
                </div>
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Service Type</span>
                  <span className="text-[#3F3F46]">SaaS platform for supported Instagram automation and messaging workflows.</span>
                </div>
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Website</span>
                  <Link href="/" className="text-[#6D28D9] font-semibold hover:underline">
                    https://comlina.ai
                  </Link>
                </div>
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Operator / Legal Name</span>
                  <span className="font-bold text-[#18181B]">Challala Kiran Sai (Comlina)</span>
                </div>
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Official Email</span>
                  <a href="mailto:kiransai.challala@gmail.com" className="text-[#6D28D9] font-semibold hover:underline">
                    kiransai.challala@gmail.com
                  </a>
                </div>
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Telephone / Helpline</span>
                  <a href="tel:+919014736476" className="text-[#6D28D9] font-semibold hover:underline">
                    +91 9014736476
                  </a>
                </div>
                <div className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="font-semibold text-[#71717A]">Business Type</span>
                  <span className="text-[#3F3F46]">Sole Proprietorship / Commercial SaaS Provider</span>
                </div>
              </div>
              <p className="text-xs text-[#71717A] leading-relaxed italic">
                Comlina&apos;s operator information reflects the legal entity actually providing the service and is consistent with applicable registration records and payment-provider verification.
              </p>
            </section>

            {/* Section 2 */}
            <section id="customer-support" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  2
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Customer Support</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">
                For general questions, technical issues, account access, and product assistance:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-1">
                  <Mail size={16} className="text-[#6D28D9]" />
                  <span className="font-semibold text-[#18181B] block">Email Support</span>
                  <a href="mailto:kiransai.challala@gmail.com" className="text-[#6D28D9] font-semibold hover:underline block truncate">
                    kiransai.challala@gmail.com
                  </a>
                  <a href="mailto:support@comlina.ai" className="text-[#71717A] hover:underline block truncate text-[11px]">
                    support@comlina.ai
                  </a>
                </div>

                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-1">
                  <Phone size={16} className="text-[#6D28D9]" />
                  <span className="font-semibold text-[#18181B] block">Phone Support</span>
                  <a href="tel:+919014736476" className="text-[#6D28D9] font-semibold hover:underline block">
                    +91 9014736476
                  </a>
                  <span className="text-[#71717A] text-[11px] block">Direct helpline &amp; WhatsApp</span>
                </div>

                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-1">
                  <Clock size={16} className="text-[#6D28D9]" />
                  <span className="font-semibold text-[#18181B] block">Support Hours</span>
                  <span className="text-[#52525B] block">
                    Mon – Sat, 9:00 AM – 7:00 PM IST (UTC+5:30)
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-1">
                  <ShieldCheck size={16} className="text-[#15803D]" />
                  <span className="font-semibold text-[#18181B] block">Response Target</span>
                  <span className="text-[#52525B] block">
                    Within 24 business hours (priority 4–6 hrs for paid plans)
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#FAF9FE] border border-[#E9E4F5] text-xs text-[#4C1D95] space-y-1">
                <p>
                  <strong>When contacting support:</strong> Please include a description of the issue and the email address associated with your Comlina workspace.
                </p>
                <p className="text-red-700 font-semibold">
                  Do not include passwords, Instagram access tokens, UPI PINs, or full payment-card details.
                </p>
              </div>
            </section>

            {/* Section 3 */}
            <section id="billing-and-payments" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  3
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Billing and Payments</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">
                For questions regarding subscriptions, payments, or invoices:
              </p>

              <div className="space-y-2.5 text-xs text-[#3F3F46]">
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5]">
                  <CreditCard size={15} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B]">Billing Email: </span>
                    <a href="mailto:billing@comlina.com" className="text-[#6D28D9] font-semibold hover:underline">
                      billing@comlina.com
                    </a>{' '}
                    (or{' '}
                    <a href="mailto:support@comlina.ai" className="text-[#6D28D9] font-semibold hover:underline">
                      support@comlina.ai
                    </a>)
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5]">
                  <ShieldCheck size={15} className="text-[#15803D] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B]">Payment Provider: </span>
                    <span>Razorpay (and supported payment rails: UPI, NetBanking, Cards).</span>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5]">
                  <FileText size={15} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B]">Available Plans: </span>
                    <span>Free (₹0), Premium (₹199 per month), and Pro (₹399 per month), as displayed on our{' '}
                      <Link href="/pricing" className="text-[#6D28D9] font-semibold hover:underline">
                        pricing page
                      </Link>.
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-xs text-[#71717A] italic leading-relaxed">
                All payments are subject to the applicable checkout terms, subscription conditions, and the{' '}
                <Link href="/refund" className="text-[#6D28D9] font-semibold underline">
                  Refund &amp; Cancellation Policy
                </Link>.
              </p>
            </section>

            {/* Section 4 */}
            <section id="privacy-requests" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  4
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Privacy Requests</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                For questions about personal information, account deletion, Instagram disconnection, or privacy complaints:
              </p>

              <div className="space-y-2.5 text-xs text-[#3F3F46]">
                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-1">
                  <span className="font-semibold text-[#18181B] block">Privacy Contact</span>
                  <a href="mailto:privacy@comlina.com" className="text-[#6D28D9] font-semibold hover:underline">
                    privacy@comlina.com
                  </a>
                </div>

                <div className="p-3.5 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] space-y-1">
                  <span className="font-semibold text-[#18181B] block">Data Protection Contact</span>
                  <span className="text-[#52525B]">Designated Data Protection &amp; Compliance Officer</span>
                  <div className="mt-0.5">
                    <a href="mailto:privacy@comlina.com" className="text-[#6D28D9] font-semibold hover:underline">
                      privacy@comlina.com
                    </a>
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#FAF9FE] border border-[#E9E4F5] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div>
                  <span className="font-semibold text-[#18181B] block">Meta Automated Data Deletion Callback</span>
                  Track the real-time status of your Meta Graph API data deletion request.
                </div>
                <Link
                  href="/data-deletion-status"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#5B21B6] hover:bg-[#4C1D95] text-white font-semibold shrink-0"
                >
                  <span>Check Status</span>
                  <ExternalLink size={12} />
                </Link>
              </div>

              <p className="text-xs text-[#71717A] italic">
                Privacy requests will be reviewed and handled according to our{' '}
                <Link href="/privacy" className="text-[#6D28D9] font-semibold underline">
                  Privacy Policy
                </Link>{' '}
                and applicable law.
              </p>
            </section>

            {/* Section 5 */}
            <section id="legal-notices" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  5
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Legal Notices</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                For legal correspondence, formal notices, or questions concerning Comlina&apos;s Terms of Service:
              </p>

              <div className="space-y-3 p-4 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] text-xs">
                <div>
                  <span className="font-semibold text-[#71717A] block">Legal Operator / Proprietor:</span>
                  <span className="font-bold text-[#18181B]">Challala Kiran Sai (Comlina)</span>
                </div>
                <div>
                  <span className="font-semibold text-[#71717A] block">Official &amp; Legal Email:</span>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 mt-0.5">
                    <a href="mailto:kiransai.challala@gmail.com" className="text-[#6D28D9] font-semibold hover:underline">
                      kiransai.challala@gmail.com
                    </a>
                    <span className="text-[#D4D4D8]">•</span>
                    <a href="mailto:legal@comlina.com" className="text-[#6D28D9] font-semibold hover:underline">
                      legal@comlina.com
                    </a>
                    <span className="text-[#D4D4D8]">•</span>
                    <a href="mailto:support@comlina.ai" className="text-[#6D28D9] font-semibold hover:underline">
                      support@comlina.ai
                    </a>
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-[#71717A] block">Official Telephone:</span>
                  <a href="tel:+919014736476" className="text-[#6D28D9] font-semibold hover:underline">
                    +91 9014736476
                  </a>
                </div>
                <div>
                  <span className="font-semibold text-[#71717A] block">Business / Correspondence Address:</span>
                  <span className="text-[#52525B]">HSR Layout, Bengaluru, Karnataka, India 560102</span>
                </div>
              </div>

              <p className="text-xs text-[#71717A] leading-relaxed">
                Please clearly identify the nature of your enquiry and provide relevant reference numbers where available.
              </p>
            </section>

            {/* Section 6 */}
            <section id="policies-and-documents" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  6
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Policies and Documents</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">Users can access all official policy documentation:</p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {[
                  {
                    title: 'Privacy Policy',
                    desc: 'Data collection, processing, and retention practices.',
                    href: '/privacy',
                  },
                  {
                    title: 'Terms & Conditions',
                    desc: 'User agreements, permitted use, and platform terms.',
                    href: '/terms',
                  },
                  {
                    title: 'Refund & Cancellation Policy',
                    desc: 'Subscriptions, renewals, cancellations, and refund rules.',
                    href: '/refund',
                  },
                  {
                    title: 'Data Deletion Status',
                    desc: 'Automated Meta platform data purge tracking portal.',
                    href: '/data-deletion-status',
                  },
                ].map((doc, idx) => (
                  <Link
                    key={idx}
                    href={doc.href}
                    className="p-3.5 rounded-xl border border-[#E4E4E7] bg-[#FAFAFA] hover:bg-white hover:border-[#6D28D9] transition-all group flex flex-col justify-between"
                  >
                    <div>
                      <div className="font-bold text-[#18181B] group-hover:text-[#6D28D9] flex items-center justify-between">
                        <span>{doc.title}</span>
                        <ArrowRight size={13} className="text-[#A1A1AA] group-hover:text-[#6D28D9] group-hover:translate-x-0.5 transition-all" />
                      </div>
                      <p className="text-[11px] text-[#71717A] mt-1 leading-relaxed">
                        {doc.desc}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </section>

            {/* Section 7 */}
            <section id="third-party-platforms" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  7
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Third-Party Platforms</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Comlina integrates with third-party services, including Instagram (Meta) and payment providers (Razorpay). Such services are governed by their own applicable terms and policies.
              </p>
              <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 leading-relaxed flex items-start gap-2.5">
                <Instagram size={16} className="text-amber-800 shrink-0 mt-0.5" />
                <span>
                  <strong>Meta Platform Disclaimer:</strong> Comlina does not claim to be owned, operated, sponsored, or endorsed by Meta unless an authorized relationship explicitly establishes otherwise.
                </span>
              </div>
            </section>

            {/* Section 8 */}
            <section id="accuracy-of-information" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  8
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Accuracy of Information</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                We aim to keep our contact and legal information accurate and up to date. If our operating entity, contact details, or service arrangements change, this page will be updated as appropriate.
              </p>
              <div className="flex items-center gap-2 text-xs font-semibold text-[#15803D] pt-1">
                <Check size={14} />
                <span>Last Updated: October 17, 2026</span>
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
            <Link href="/refund" className="hover:text-[#18181B] transition-colors">
              Refund &amp; Cancellation Policy
            </Link>
            <Link href="/contact" className="text-[#18181B] font-semibold">
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
