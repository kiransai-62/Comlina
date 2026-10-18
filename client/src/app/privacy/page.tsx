// client/src/app/privacy/page.tsx
import React from 'react';
import Link from 'next/link';
import { 
  Shield, 
  ArrowLeft, 
  Lock, 
  FileText, 
  Users, 
  Globe, 
  Mail, 
  Phone,
  Trash2, 
  CreditCard, 
  ExternalLink, 
  ChevronRight, 
  Instagram, 
  ShieldCheck, 
  Check 
} from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

export const metadata = {
  title: 'Privacy Policy | Comlina',
  description: 'Privacy Policy and data governance documentation for Comlina Instagram Automation Platform',
};

const SECTIONS = [
  { id: 'introduction', number: '1', title: 'Introduction' },
  { id: 'information-we-collect', number: '2', title: 'Information We Collect' },
  { id: 'how-we-use-information', number: '3', title: 'How We Use Information' },
  { id: 'legal-grounds', number: '4', title: 'Legal Grounds & Consent' },
  { id: 'third-party-services', number: '5', title: 'Instagram & Third-Party Services' },
  { id: 'sharing-information', number: '6', title: 'Sharing of Information' },
  { id: 'data-retention', number: '7', title: 'Data Retention' },
  { id: 'data-security', number: '8', title: 'Data Security' },
  { id: 'privacy-rights', number: '9', title: 'Your Privacy Rights' },
  { id: 'account-deletion', number: '10', title: 'Account Deletion & Disconnection' },
  { id: 'childrens-privacy', number: '11', title: "Children's Privacy" },
  { id: 'international-data', number: '12', title: 'International Data Processing' },
  { id: 'policy-changes', number: '13', title: 'Changes to This Policy' },
  { id: 'contact-information', number: '14', title: 'Contact Information' },
];

export default function PrivacyPolicyPage() {
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
            <span>Official Policy &amp; Compliance</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#18181B]">
            Privacy Policy
          </h1>
          <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs font-medium text-[#71717A] mt-3">
            <span><strong>Effective Date:</strong> October 17, 2026</span>
            <span className="text-[#D4D4D8]">•</span>
            <span><strong>Last Updated:</strong> October 17, 2026</span>
            <span className="text-[#D4D4D8]">•</span>
            <span className="text-[#15803D] flex items-center gap-1 font-semibold">
              <ShieldCheck size={13} /> Meta Graph API & Razorpay Compliant
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
                  <Trash2 size={15} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold text-[#5B21B6]">Data Deletion Request?</h4>
                    <p className="text-[11px] text-[#71717A] mt-0.5">
                      Check your request or submit one via our portal.
                    </p>
                    <Link
                      href="/data-deletion-status"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#6D28D9] hover:underline mt-1.5"
                    >
                      <span>Check Deletion Status</span>
                      <ExternalLink size={11} />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          {/* Privacy Content Area */}
          <main className="lg:col-span-8 space-y-6">
            {/* Section 1 */}
            <section id="introduction" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  1
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Introduction</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Welcome to Comlina (&ldquo;Comlina,&rdquo; &ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;). Comlina is a software-as-a-service platform designed to help creators, businesses, and marketers manage supported Instagram comment-to-DM automations and related workflows.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                This Privacy Policy explains what information we collect, how we use it, when we share it, and how users can exercise their privacy rights.
              </p>
              <div className="p-3.5 rounded-xl bg-[#FAF9FE] border border-[#E9E4F5] text-xs font-medium text-[#4C1D95]">
                By using Comlina, you acknowledge that you have read and understood this policy.
              </div>
            </section>

            {/* Section 2 */}
            <section id="information-we-collect" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-5 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  2
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Information We Collect</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">
                Depending on the features you use, we may collect the following categories of information:
              </p>

              <div className="space-y-4 text-sm">
                <div className="border border-[#F4F4F5] bg-[#FAFAFA] rounded-xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B] mb-2 flex items-center gap-1.5">
                    <Users size={14} className="text-[#6D28D9]" />
                    2.1 Account Information
                  </h3>
                  <ul className="list-disc pl-5 space-y-1.5 text-xs text-[#52525B]">
                    <li>Name and email address.</li>
                    <li>Authentication credentials and account security information.</li>
                    <li>Subscription plan and account preferences.</li>
                    <li>Support requests, feedback, and customer communications.</li>
                  </ul>
                </div>

                <div className="border border-[#F4F4F5] bg-[#FAFAFA] rounded-xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B] mb-2 flex items-center gap-1.5">
                    <Instagram size={14} className="text-[#6D28D9]" />
                    2.2 Instagram and Integration Information
                  </h3>
                  <p className="text-xs text-[#52525B] mb-2">
                    When you connect an Instagram account, Comlina may process information authorized through Meta&apos;s official APIs, including:
                  </p>
                  <ul className="list-disc pl-5 space-y-1.5 text-xs text-[#52525B]">
                    <li>Instagram account identifiers, usernames, and permitted profile information.</li>
                    <li>Comments and related content required to configure and trigger automations.</li>
                    <li>Message delivery status and supported conversation telemetry.</li>
                    <li>Automation settings, trigger keywords, and response templates.</li>
                  </ul>
                  <p className="text-[11px] text-[#71717A] mt-2 italic">
                    The specific information available depends on the permissions granted, the connected account, and Meta&apos;s API capabilities.
                  </p>
                </div>

                <div className="border border-[#F4F4F5] bg-[#FAFAFA] rounded-xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B] mb-2 flex items-center gap-1.5">
                    <FileText size={14} className="text-[#6D28D9]" />
                    2.3 Usage and Technical Information
                  </h3>
                  <p className="text-xs text-[#52525B]">
                    We may collect service usage records, feature interactions, error reports, timestamps, browser/device diagnostics, and technical telemetry needed to operate, secure, and improve the platform.
                  </p>
                </div>

                <div className="border border-[#F4F4F5] bg-[#FAFAFA] rounded-xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#18181B] mb-2 flex items-center gap-1.5">
                    <CreditCard size={14} className="text-[#6D28D9]" />
                    2.4 Payment Information
                  </h3>
                  <p className="text-xs text-[#52525B] leading-relaxed">
                    Payments may be processed through third-party payment providers, such as Razorpay, if enabled.
                  </p>
                  <p className="text-xs text-[#52525B] mt-2 leading-relaxed">
                    We may receive transaction references, payment status, subscription details, and billing records. Payment card details and other sensitive payment credentials should be handled by the payment provider rather than stored directly by Comlina, unless a separately disclosed and appropriately secured arrangement applies.
                  </p>
                </div>
              </div>
            </section>

            {/* Section 3 */}
            <section id="how-we-use-information" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  3
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">How We Use Information</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">We use information as necessary to:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs text-[#3F3F46]">
                {[
                  'Create and maintain user accounts.',
                  'Connect supported integrations.',
                  'Execute user-configured automations.',
                  'Deliver and troubleshoot platform features.',
                  'Process subscriptions and payments.',
                  'Enforce plan limits and prevent abuse.',
                  'Respond to support requests.',
                  'Protect accounts and investigate security incidents.',
                  'Meet applicable legal and regulatory obligations.',
                  'Improve the reliability and performance of Comlina.',
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-[#FAF9F7] border border-[#F4F4F5]">
                    <Check size={14} className="text-[#15803D] shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[#71717A] italic pt-1">
                We do not promise that every feature will be available for every Instagram account or API permission level.
              </p>
            </section>

            {/* Section 4 */}
            <section id="legal-grounds" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  4
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Legal Grounds and Consent</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Where applicable law requires a legal basis for processing, Comlina will rely on an appropriate basis, such as fulfilling a contract, complying with legal obligations, obtaining consent, or pursuing legitimate interests permitted by law.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Where required, we will obtain consent before processing information for the relevant purpose.
              </p>
            </section>

            {/* Section 5 */}
            <section id="third-party-services" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  5
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Instagram and Third-Party Services</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Comlina may depend on services operated by Meta, payment providers, hosting companies, databases, email services, and other infrastructure providers.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Those services may process information under their own terms and privacy policies. Your use of Instagram remains subject to Meta&apos;s applicable terms and policies.
              </p>
              <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 leading-relaxed">
                Comlina does not control third-party platform availability, API changes, permission restrictions, or account decisions made by Meta or other third-party providers.
              </div>
            </section>

            {/* Section 6 */}
            <section id="sharing-information" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  6
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Sharing of Information</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">We may share information with:</p>
              <ul className="list-disc pl-5 space-y-2 text-xs text-[#52525B]">
                <li>Service providers necessary to operate Comlina (hosting, database, infrastructure).</li>
                <li>Instagram or Meta, as required to provide authorized integrations.</li>
                <li>Payment providers (such as Razorpay) for transaction processing.</li>
                <li>Professional advisers where appropriate (legal, auditing, accounting).</li>
                <li>Authorities when legally required by applicable statute, court order, or regulation.</li>
                <li>Relevant parties in a business transfer, subject to applicable law.</li>
              </ul>
              <div className="p-3.5 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-xs font-semibold text-[#15803D]">
                We do not sell personal information as a business model. We will not disclose information for unrelated purposes without an appropriate legal basis.
              </div>
            </section>

            {/* Section 7 */}
            <section id="data-retention" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  7
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Data Retention</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                We retain information only for as long as reasonably necessary for the purposes described in this policy, including providing the service, maintaining legitimate business records, resolving disputes, and complying with legal obligations.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Retention periods depend on the type of information and the purpose for which it is used.
              </p>
            </section>

            {/* Section 8 */}
            <section id="data-security" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  8
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Data Security</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                We use appropriate technical and organizational measures designed to protect information against unauthorized access, loss, alteration, and disclosure.
              </p>
              <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-[#FAF9FE] border border-[#E9E4F5] text-xs text-[#4C1D95]">
                <Lock size={15} className="shrink-0 mt-0.5 text-[#6D28D9]" />
                <span>
                  No internet-based service can guarantee absolute security. Users should protect their account credentials and notify us immediately if they suspect unauthorized access.
                </span>
              </div>
            </section>

            {/* Section 9 */}
            <section id="privacy-rights" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  9
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Your Privacy Rights</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">
                Depending on applicable law (such as GDPR, CCPA, or applicable Indian data protection laws), you may have rights to:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#52525B]">
                {[
                  'Request access to personal information.',
                  'Request correction of inaccurate information.',
                  'Request deletion of eligible information.',
                  'Withdraw consent where processing relies on consent.',
                  'Object to or restrict certain processing.',
                  'Request a copy of eligible information.',
                  'Submit a privacy complaint to the appropriate authority.',
                ].map((right, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-[#FAF9F7] border border-[#F4F4F5]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#6D28D9]"></span>
                    <span>{right}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[#71717A] pt-1">
                To exercise any of these rights, please contact us using the details in the{' '}
                <a href="#contact-information" className="text-[#6D28D9] font-semibold underline">
                  Contact Information section
                </a>.
              </p>
            </section>

            {/* Section 10 */}
            <section id="account-deletion" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  10
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Account Deletion and Instagram Disconnection</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Users may request account deletion or disconnect an Instagram integration through available account settings or by contacting support.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Disconnecting Instagram stops the corresponding integration where technically supported. It may not automatically delete all previously stored records.
              </p>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                When an eligible deletion request is received, we will process it according to our retention practices and applicable law, subject to lawful exceptions.
              </p>
              <div className="p-4 rounded-xl bg-[#FAF9FE] border border-[#E9E4F5] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="text-xs text-[#3F3F46]">
                  <span className="font-semibold text-[#18181B] block">Data Deletion Status Tracker</span>
                  Track the status of any Meta platform automated data deletion callback.
                </div>
                <Link
                  href="/data-deletion-status"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#5B21B6] text-white hover:bg-[#4C1D95] transition-colors shrink-0"
                >
                  <span>View Status Portal</span>
                  <ExternalLink size={12} />
                </Link>
              </div>
            </section>

            {/* Section 11 */}
            <section id="childrens-privacy" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  11
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Children&apos;s Privacy</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Comlina is not intended for individuals who are not legally permitted to enter into the applicable agreement or use the service under relevant law. We do not knowingly collect personal information from children in violation of applicable legal requirements.
              </p>
            </section>

            {/* Section 12 */}
            <section id="international-data" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  12
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">International Data Processing</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                Depending on the infrastructure and providers used, information may be processed or stored in different jurisdictions. Where required, appropriate safeguards will be applied to such processing.
              </p>
            </section>

            {/* Section 13 */}
            <section id="policy-changes" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-4 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  13
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Changes to This Policy</h2>
              </div>
              <p className="text-sm leading-relaxed text-[#3F3F46]">
                We may update this policy when our services, practices, or legal obligations change. The updated version will be published on this page with a revised date where appropriate.
              </p>
            </section>

            {/* Section 14 */}
            <section id="contact-information" className="bg-white border border-[#E4E4E7] rounded-2xl p-6 sm:p-8 space-y-5 shadow-2xs scroll-mt-24">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#6D28D9] font-bold text-xs flex items-center justify-center">
                  14
                </span>
                <h2 className="text-lg font-bold text-[#18181B]">Contact Information</h2>
              </div>
              <p className="text-sm text-[#3F3F46]">
                For privacy questions, data requests, or complaints, contact:
              </p>

              <div className="space-y-3 p-4 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5] text-xs">
                <div className="flex items-start gap-2.5">
                  <Shield size={16} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B] block">Operator / Legal Name:</span>
                    <span className="font-semibold text-[#18181B]">Challala Kiran Sai (Comlina)</span>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <Mail size={16} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B] block">Official Privacy &amp; Support Email:</span>
                    <div className="flex flex-wrap gap-x-3 gap-y-1 mt-0.5">
                      <a href="mailto:kiransai.challala@gmail.com" className="text-[#6D28D9] hover:underline font-semibold">
                        kiransai.challala@gmail.com
                      </a>
                      <span className="text-[#D4D4D8]">•</span>
                      <a href="mailto:support@comlina.ai" className="text-[#6D28D9] hover:underline font-semibold">
                        support@comlina.ai
                      </a>
                      <span className="text-[#D4D4D8]">•</span>
                      <a href="mailto:privacy@comlina.com" className="text-[#6D28D9] hover:underline font-semibold">
                        privacy@comlina.com
                      </a>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <Phone size={16} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B] block">Contact Telephone:</span>
                    <a href="tel:+919014736476" className="text-[#6D28D9] hover:underline font-semibold">
                      +91 9014736476
                    </a>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <Globe size={16} className="text-[#6D28D9] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[#18181B] block">Business Address:</span>
                    <span className="text-[#52525B]">HSR Layout, Bengaluru, Karnataka, India 560102</span>
                  </div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-red-50/70 border border-red-200/60 text-xs text-red-900 leading-relaxed">
                <strong>Security Reminder:</strong> Please do not include passwords, API access tokens, or payment credentials in support or privacy correspondence.
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
            <Link href="/privacy" target="_blank" rel="noopener noreferrer" className="text-[#18181B] font-semibold">
              Privacy Policy
            </Link>
            <Link href="/terms" target="_blank" rel="noopener noreferrer" className="hover:text-[#18181B] transition-colors">
              Terms of Service
            </Link>
            <Link href="/refund" target="_blank" rel="noopener noreferrer" className="hover:text-[#18181B] transition-colors">
              Refund Policy
            </Link>
            <Link href="/contact" className="hover:text-[#18181B] transition-colors">
              Contact &amp; Legal
            </Link>
            <Link href="/data-deletion-status" target="_blank" rel="noopener noreferrer" className="hover:text-[#18181B] transition-colors">
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
