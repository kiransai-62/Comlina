// client/src/app/terms/page.tsx
import React from 'react';
import Link from 'next/link';
import { FileText, ArrowLeft, AlertCircle } from 'lucide-react';
import { BrandLogo } from '@/components/BrandLogo';

export const metadata = {
  title: 'Terms of Service | Comlina',
  description: 'Terms of Service for Comlina Instagram Automation Platform',
};

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-[#FBFBFA] text-[#111110]">
      {/* Navigation Header */}
      <header className="border-b border-[#ECECE8] bg-white sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <BrandLogo variant="full" height={28} />
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#70706B] hover:text-[#111110] transition-colors"
          >
            <ArrowLeft size={14} />
            <span>Back to Comlina</span>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-8">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#EAF6EE] text-[#15803D] rounded-full text-xs font-semibold mb-3">
            <FileText size={13} />
            <span>Legal Documentation</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Terms of Service</h1>
          <p className="text-xs text-[#70706B] mt-1.5">Last updated: October 2026</p>
        </div>

        {/* Legal Review Disclaimer */}
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-3">
          <AlertCircle size={18} className="text-amber-700 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 leading-relaxed">
            <span className="font-bold uppercase tracking-wider block mb-1">
              [Notice: Placeholder Marked for Legal Review]
            </span>
            These Terms of Service are a draft placeholder document currently undergoing formal legal and regulatory review. Final terms will be promulgated prior to public production deployment.
          </div>
        </div>

        <div className="bg-white border border-[#ECECE8] rounded-2xl p-6 sm:p-8 space-y-8 text-sm leading-relaxed text-[#333330]">
          <section className="space-y-3">
            <h2 className="text-base font-bold text-[#111110]">1. Acceptance of Terms</h2>
            <p>
              By creating an account, accessing, or using Comlina, you agree to be bound by these Terms of Service. If you do not agree to these terms, you must not use our software or platform.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-bold text-[#111110]">2. Permitted Use &amp; Instagram Business Account Requirement</h2>
            <p>
              Comlina operates exclusively in connection with Instagram Business and Creator accounts connected via the official Meta Graph API. You represent and warrant that:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-xs text-[#555550]">
              <li>You possess lawful authority to manage the connected Instagram account.</li>
              <li>You will not use the service to send spam, fraudulent content, deceptive phishing messages, or abusive communications.</li>
              <li>Your message automations will comply with Meta&apos;s 24-hour customer messaging policy and rate limits.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-bold text-[#111110]">3. Account Security &amp; Credentials</h2>
            <p>
              You are responsible for maintaining the confidentiality of your credentials and access tokens. You must immediately notify Comlina of any suspected unauthorized access to your account or workspace.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-bold text-[#111110]">4. Intellectual Property &amp; User Content</h2>
            <p>
              You retain ownership of all content, marketing copy, and assets configured within your automation flows. Comlina retains all rights, title, and interest in and to the platform, code, logos, and infrastructure.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-bold text-[#111110]">5. Disclaimer of Warranties &amp; Limitation of Liability</h2>
            <p>
              The platform is provided &ldquo;as is&rdquo; without warranties of any kind. Comlina is not liable for Meta API downtime, Instagram rate limit restrictions, account suspension arising from user abuse, or lost profits.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-bold text-[#111110]">6. Contact &amp; Legal Notices</h2>
            <div className="text-xs text-[#555550] space-y-1.5 p-4 rounded-xl bg-[#FAFAFA] border border-[#F4F4F5]">
              <p>
                <strong className="text-[#18181B]">Operator / Legal Entity:</strong> Challala Kiran Sai (Comlina)
              </p>
              <p>
                <strong className="text-[#18181B]">Official Contact Email:</strong>{' '}
                <a href="mailto:kiransai.challala@gmail.com" className="text-[#15803D] font-semibold hover:underline">
                  kiransai.challala@gmail.com
                </a>{' '}
                (or{' '}
                <a href="mailto:support@comlina.ai" className="text-[#15803D] font-semibold hover:underline">
                  support@comlina.ai
                </a>)
              </p>
              <p>
                <strong className="text-[#18181B]">Telephone / Helpline:</strong>{' '}
                <a href="tel:+919014736476" className="text-[#15803D] font-semibold hover:underline">
                  +91 9014736476
                </a>
              </p>
              <p>
                <strong className="text-[#18181B]">Address:</strong> HSR Layout, Bengaluru, Karnataka, India 560102
              </p>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#ECECE8] bg-white py-8 mt-12 text-xs text-[#71717A]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} Comlina. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <Link href="/privacy" className="hover:text-[#111110] transition-colors">
              Privacy Policy
            </Link>
            <Link href="/terms" className="text-[#111110] font-semibold">
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
            <Link href="/pricing" className="hover:text-[#111110] transition-colors">
              Pricing
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
