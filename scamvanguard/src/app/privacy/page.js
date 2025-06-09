import Link from 'next/link';
import Footer from '../components/Footer';

export default function Privacy() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <h1 className="text-xl font-semibold text-gray-900">ScamVanguard</h1>
            </Link>
            <a
              href="https://www.buymeacoffee.com/haydencj"
              target="_blank"
              rel="noopener noreferrer"
              className="text-md font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Donate
            </a>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Privacy Policy</h1>
        
        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-6">
            Last updated: June 7, 2025
          </p>

          <p className="text-gray-600 mb-8">
            ScamVanguard is committed to protecting your privacy. This policy explains how we handle your data when you use our free scam detection service.
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Our Privacy Promise</h2>
            <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
              <p className="text-gray-700">
                <strong>All emails and attachments are automatically deleted after 24 hours.</strong> We don&apos;t keep your data longer than necessary to provide the service.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">What Data We Collect</h2>
            <p className="text-gray-600 mb-4">When you forward an email to scan@scamvanguard.com, we temporarily collect:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600 mb-4">
              <li>Your email address (to send the response back to you)</li>
              <li>The forwarded email content and any attachments</li>
              <li>Email metadata (subject line, timestamps)</li>
            </ul>
            <p className="text-gray-600 mb-4">We do NOT collect:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Your name or personal information (unless included in the forwarded content)</li>
              <li>Your location or IP address</li>
              <li>Any tracking cookies or browser data</li>
              <li>Payment information (the service is free)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">How We Use Your Data</h2>
            <p className="text-gray-600 mb-4">We use the collected data solely to:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Analyze the forwarded content for scam indicators using AI</li>
              <li>Send you a response with our SAFE/SCAM verdict</li>
              <li>Monitor aggregate service metrics (total emails processed, not individual data)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Data Retention</h2>
            <div className="bg-gray-50 rounded-lg p-6 mb-4">
              <h3 className="font-semibold text-gray-900 mb-2">24-Hour Automatic Deletion</h3>
              <p className="text-gray-600">
                All emails, attachments, and associated data are automatically deleted from our systems 24 hours after receipt. This deletion is enforced by AWS S3 lifecycle policies and cannot be overridden.
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-2">Aggregate Metrics</h3>
              <p className="text-gray-600">
                We keep anonymous aggregate metrics (like total daily email count) for 7 days to monitor service health. These metrics contain no personal information.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Third-Party Services</h2>
            <p className="text-gray-600 mb-4">ScamVanguard uses the following services to operate:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li><strong>Amazon Web Services (AWS)</strong> - For email processing and temporary storage</li>
              <li><strong>OpenAI GPT-4</strong> - For AI-powered scam analysis</li>
              <li><strong>Twilio</strong> - For SMS support (coming soon)</li>
            </ul>
            <p className="text-gray-600 mt-4">
              These services process data according to their own privacy policies. We&apos;ve configured them to minimize data retention and maximize security.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Your Rights</h2>
            <p className="text-gray-600 mb-4">You have the right to:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li><strong>Unsubscribe</strong> - Stop receiving responses from our service</li>
              <li><strong>Data Deletion</strong> - Though all data is automatically deleted after 24 hours</li>
              <li><strong>Information</strong> - Ask questions about how we handle your data</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Email Suppression & Unsubscribe</h2>
            <p className="text-gray-600 mb-4">
              If you wish to stop receiving responses from ScamVanguard:
            </p>
            <ol className="list-decimal pl-6 space-y-2 text-gray-600 mb-4">
              <li>Reply &quot;STOP&quot; to any ScamVanguard email</li>
              <li>Or visit our <Link href="/unsubscribe" className="text-blue-600 hover:underline">unsubscribe page</Link></li>
            </ol>
            <p className="text-gray-600">
              Your email will be added to our suppression list, and you&apos;ll receive a confirmation. You can resubscribe at any time by forwarding a new email to our service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">GDPR & CCPA Compliance</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">GDPR (European Users)</h3>
                <p className="text-gray-600">
                  We process data under legitimate interest to provide our free scam detection service. You can exercise your GDPR rights by contacting us. However, since all data is deleted within 24 hours, most rights are automatically fulfilled.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">CCPA (California Users)</h3>
                <p className="text-gray-600">
                  We don&apos;t sell personal information. California residents have the right to know what data we collect (detailed above) and to opt-out of the service at any time.
                </p>
              </div>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Children&apos;s Privacy</h2>
            <p className="text-gray-600">
              ScamVanguard is not intended for use by children under 13. We don&apos;t knowingly collect data from children. If you believe a child has used our service, please contact us.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Changes to This Policy</h2>
            <p className="text-gray-600">
              We may update this privacy policy from time to time. The &quot;Last updated&quot; date at the top shows when it was last revised. Continued use of the service after changes constitutes acceptance.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Contact Us</h2>
            <p className="text-gray-600">
              If you have questions about this privacy policy or how we handle your data, please email us at:
            </p>
            <p className="mt-2">
              <a href="mailto:contact@scamvanguard.com" className="text-blue-600 hover:underline">
                contact@scamvanguard.com
              </a>
            </p>
          </section>
        </div>
      </div>

      {/* Footer */}
      <Footer/>
    </div>
  );
}