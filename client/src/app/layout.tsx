import '@/styles/globals.css';
import type { Metadata } from 'next';
import { PwaInstallPrompt } from '@/features/pwa/PwaInstallPrompt';

export const metadata: Metadata = {
  title: 'Comlina — Turn Conversations into Growth',
  description: 'Turn Conversations into Growth. Turn comments, story replies, and mentions into qualified leads and sales with Instagram automation.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Comlina',
  },
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon.png', type: 'image/png' },
      { url: '/icon.png', type: 'image/png' },
    ],
    shortcut: '/favicon.ico',
    apple: [
      { url: '/apple-icon.png' },
      { url: '/comlina-mark.png' },
    ],
  },
  other: {
    'google-adsense-account': 'ca-pub-2835160283629906',
  },
};

// viewport-fit=cover lets content reach the edges under notches/home
// indicators on mobile, in exchange for us handling safe-area insets
// ourselves in globals.css.
export const viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover' as const,
  themeColor: '#064125',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2835160283629906"
          crossOrigin="anonymous"
        />
      </head>
      <body className="bg-[#FAFAF8] min-h-screen text-[#333330] antialiased">
        {children}
        <PwaInstallPrompt />
      </body>
    </html>
  );
}
