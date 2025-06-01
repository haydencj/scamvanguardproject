import { Analytics } from '@vercel/analytics/next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "ScamVanguard",
    "description": "Free scam detection service that instantly checks if emails and texts are scams",
    "applicationCategory": "SecurityApplication",
    "url": "https://scamvanguard.com",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "featureList": [
      "Email scam detection",
      "SMS/MMS scam detection", 
      "Instant results",
      "No app download required"
    ],
    "creator": {
      "@type": "Person",
      "name": "Hayden Johnson"
    }
  };
  
export const metadata = {
  metadataBase: new URL('https://scamvanguard.com'),
  title: {
    default: 'ScamVanguard - Free Scam Detection Service',
    template: '%s | ScamVanguard'
  },
  description: 'Forward suspicious emails and texts to get instant SAFE/SCAM verdicts. Free scam detection service for seniors and non-technical users.',
  keywords: ['scam detection', 'email scam checker', 'text scam checker', 'phishing detection', 'senior scam protection'],
  openGraph: {
    title: 'ScamVanguard - Protect Yourself from Scams',
    description: 'Free, instant scam detection. Forward suspicious messages to get SAFE/SCAM verdicts.',
    images: ['/og-image.png'],
    url: 'https://scamvanguard.com',
    siteName: 'ScamVanguard',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ScamVanguard - Free Scam Detection',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        {/* Add the structured data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>
      <body className={inter.className}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}