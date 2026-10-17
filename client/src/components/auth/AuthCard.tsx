import Image from 'next/image';
import type { ReactNode } from 'react';

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="flex min-h-[100dvh] flex-col lg:flex-row">
      {/* Brand panel — hidden below lg. This is the one place the full
          gradient shows at scale, per "accent, not everywhere". */}
      <div className="relative hidden shrink-0 flex-col justify-between overflow-hidden bg-[#003018] p-10 lg:flex lg:w-[42%] xl:w-[38%]">
        <div
          className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-30 blur-3xl"
          style={{
            background:
              'radial-gradient(circle, #7030F0 0%, #F02070 45%, #F0A020 100%)',
          }}
          aria-hidden="true"
        />
        <div className="flex items-center gap-2">
          <Image src="/comlina-mark.png" alt="" width={32} height={32} />
          <span className="text-lg font-semibold text-white">Comlina</span>
        </div>
        <div className="relative">
          <p className="text-2xl font-medium leading-snug text-white xl:text-3xl">
            Turn conversations
            <br />
            into growth.
          </p>
          <p className="mt-3 max-w-xs text-sm text-white/60">
            Automate replies, qualify leads, and convert followers — all from
            your DMs.
          </p>
        </div>
      </div>

      {/* Form panel — full width on mobile/tablet, remaining width on lg+ */}
      <div className="flex flex-1 items-center justify-center bg-[#FAFAF8] px-4 py-10 sm:px-6 lg:px-10">
        <div className="w-full max-w-sm rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm sm:p-8">
          {/* Logo shown here only below lg, since the brand panel covers it above */}
          <div className="mb-6 flex flex-col items-center gap-1 text-center lg:hidden">
            <Image src="/comlina-mark.png" alt="Comlina" width={36} height={36} priority />
          </div>
          <div className="mb-6 text-center lg:text-left">
            <h1 className="text-lg font-semibold text-neutral-900 sm:text-xl">{title}</h1>
            {subtitle && <p className="mt-1 text-sm text-neutral-500">{subtitle}</p>}
          </div>
          <div className="flex flex-col gap-4">{children}</div>
          {footer && (
            <div className="mt-6 text-center text-sm text-neutral-500 lg:text-left">{footer}</div>
          )}
        </div>
      </div>
    </div>
  );
}
