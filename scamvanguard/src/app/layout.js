import { Analytics } from '@vercel/analytics/next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'ScamVanguard - Free Email Scam Detection',
  description: 'Protect yourself from scams. Forward suspicious emails to get instant SAFE or SCAM verdicts. Simple, free, and designed for everyone.',
  keywords: 'scam detection, email scam, phishing protection, free scam checker',
  openGraph: {
    title: 'ScamVanguard - Free Email Scam Detection',
    description: 'Forward suspicious emails to get instant SAFE or SCAM verdicts.',
    url: 'https://scamvanguard.com',
    siteName: 'ScamVanguard',
    type: 'website',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <Analytics/>
      </body>
    </html>
  );
}