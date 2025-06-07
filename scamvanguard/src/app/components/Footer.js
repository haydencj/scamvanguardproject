// src/components/Footer.js
import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 mt-16">
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="text-center md:text-left mb-4 md:mb-0">
            <p className="text-gray-600 text-sm">
              © 2025 ScamVanguard. A non-profit service by Hayden Johnson.
            </p>
          </div>
          <div className="flex items-center space-x-6">
            <Link href="/privacy" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Privacy
            </Link>
            <Link href="/terms" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Terms
            </Link>
            <Link href="/unsubscribe" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Unsubscribe
            </Link>
            <a href="mailto:contact@scamvanguard.com" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}