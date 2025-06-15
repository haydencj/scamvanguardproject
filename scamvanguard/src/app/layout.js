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
    description: 'Free, instant scam detection. Forward suspicious messages to get SAFE/SCAM verdicts. Protect yourself and family from email fraud.',
    images: [
      {
        url: '/facebook-post.png',
        width: 1200,
        height: 630,
        alt: 'ScamVanguard - Shield protecting against email scams',
      }
    ],
    url: 'https://scamvanguard.com',
    siteName: 'ScamVanguard',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ScamVanguard - Free Scam Detection',
    description: 'Forward suspicious emails and texts to get instant SAFE/SCAM verdicts. Free protection from email fraud.',
    images: ['/facebook-post.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
  // Additional meta tags for better social sharing
  other: {
    'theme-color': '#2563eb', // Blue color for mobile browser chrome
    'apple-mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-status-bar-style': 'default',
  }
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
        {/* Favicon and apple touch icons */}
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
      </head>
      <body className={inter.className}>
        {children}
        <Analytics />
      </body>
    </html>
  );
}