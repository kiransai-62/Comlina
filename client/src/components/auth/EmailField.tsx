'use client';

export function EmailField({
  id = 'email',
  label = 'Email',
  value,
  onChange,
  error,
}: {
  id?: string;
  label?: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-neutral-700">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type="email"
        inputMode="email"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="email"
        required
        placeholder="kiran.sai@comlina.com"
        // py-3 keeps a ≥44px touch target on mobile; sm:py-2.5 tightens it
        // back up once a mouse/trackpad is the likely input device.
        className="w-full rounded-xl border border-neutral-200 bg-white px-4 py-3 text-neutral-900 outline-none transition focus:border-[#004020] focus:ring-2 focus:ring-[#004020]/20 sm:py-2.5"
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
