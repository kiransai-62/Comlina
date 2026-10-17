'use client';

import { useState } from 'react';

export function PasswordField({
  id = 'password',
  label = 'Password',
  value,
  onChange,
  autoComplete = 'current-password',
  error,
}: {
  id?: string;
  label?: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete?: 'current-password' | 'new-password';
  error?: string;
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-neutral-700">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          id={id}
          name={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          required
          placeholder="••••••••"
          minLength={autoComplete === 'new-password' ? 6 : undefined}
          className="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 pr-12 text-neutral-900 outline-none transition focus:border-[#004020] focus:ring-2 focus:ring-[#004020]/20 sm:py-2.5 sm:pr-11"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide password' : 'Show password'}
          // 44px hit area on mobile via padding, not just the emoji glyph
          className="absolute right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center text-neutral-400 hover:text-neutral-600 sm:h-9 sm:w-9"
        >
          {visible ? '🙈' : '👁️'}
        </button>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
