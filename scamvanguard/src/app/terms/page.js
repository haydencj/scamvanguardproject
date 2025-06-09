import Link from 'next/link';
import Footer from './components/Footer';

export default function Terms() {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Terms of Service</h1>
        
        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-6">
            Last updated: June 7, 2025
          </p>

          <p className="text-gray-600 mb-8">
            Welcome to ScamVanguard. By using our service, you agree to these terms. Please read them carefully.
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Service Description</h2>
            <p className="text-gray-600 mb-4">
              ScamVanguard is a free service that analyzes forwarded emails and messages to help identify potential scams. The service provides educational assessments using artificial intelligence to evaluate content for common scam indicators.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Acceptable Use</h2>
            <p className="text-gray-600 mb-4">You agree to use ScamVanguard only for:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600 mb-4">
              <li>Checking suspicious emails, texts, or messages you&apos;ve personally received</li>
              <li>Educational purposes to learn about scam tactics</li>
              <li>Helping friends or family members check suspicious content</li>
            </ul>
            <p className="text-gray-600 mb-4">You agree NOT to:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Send spam or bulk emails to our service</li>
              <li>Use the service to harass or harm others</li>
              <li>Attempt to overload or disrupt the service</li>
              <li>Forward content containing illegal material</li>
              <li>Use the service for commercial purposes without permission</li>
              <li>Attempt to reverse engineer or copy the service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. Service Limitations</h2>
            <div className="bg-yellow-50 border-l-4 border-yellow-600 p-4 mb-6">
              <p className="text-gray-700">
                <strong>Daily Limit:</strong> The service is limited to 500 total requests per day across all users. During high-demand periods, you may receive a message that the service is temporarily unavailable.
              </p>
            </div>
            <p className="text-gray-600 mb-4">Additional limitations:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>English language support only (other languages coming soon)</li>
              <li>Email size limit of 25MB including attachments</li>
              <li>Response time typically within 10 minutes, but not guaranteed</li>
              <li>Service availability is provided "as-is" without uptime guarantees</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. AI Analysis Disclaimer</h2>
            <div className="bg-red-50 border-l-4 border-red-600 p-4 mb-6">
              <p className="text-gray-700">
                <strong>Important:</strong> ScamVanguard uses artificial intelligence (AI) to analyze content. While we strive for accuracy, AI analysis is not perfect and should not be your only source of verification.
              </p>
            </div>
            <p className="text-gray-600 mb-4">Please understand that:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>AI analysis may occasionally produce incorrect results</li>
              <li>New or sophisticated scams might not be detected</li>
              <li>Legitimate emails might occasionally be flagged as suspicious</li>
              <li>The service provides educational assessments, not definitive legal or financial advice</li>
              <li>You should always use common sense and additional verification for important decisions</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. User Responsibilities</h2>
            <p className="text-gray-600 mb-4">By using ScamVanguard, you acknowledge and agree that:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>You are responsible for the content you submit to the service</li>
              <li>You won&apos;t submit content that violates others&apos; privacy or rights</li>
              <li>You&apos;ll use the service&apos;s assessments as one factor in your decision-making, not the sole factor</li>
              <li>You won&apos;t hold ScamVanguard liable for decisions made based on our analysis</li>
              <li>You&apos;ll report any service issues or errors you discover</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Privacy and Data Handling</h2>
            <p className="text-gray-600 mb-4">
              Your privacy is important to us. By using the service, you agree to our <Link href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</Link>, which explains how we handle your data. Key points:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>All emails are automatically deleted after 24 hours</li>
              <li>We don&apos;t sell or share your personal information</li>
              <li>We use secure, encrypted connections for all data transmission</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Disclaimer of Warranties</h2>
            <p className="text-gray-600 mb-4">
              ScamVanguard is provided "AS IS" and "AS AVAILABLE" without warranties of any kind, either express or implied, including but not limited to:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Accuracy or reliability of scam detection</li>
              <li>Uninterrupted or error-free service</li>
              <li>Fitness for a particular purpose</li>
              <li>Protection against all scams or fraudulent content</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Limitation of Liability</h2>
            <p className="text-gray-600 mb-4">
              To the maximum extent permitted by law, ScamVanguard and its creator shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Financial losses from scams we failed to detect</li>
              <li>Missed opportunities from legitimate emails flagged as scams</li>
              <li>Data loss or service interruptions</li>
              <li>Any damages arising from your use or inability to use the service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Indemnification</h2>
            <p className="text-gray-600">
              You agree to indemnify and hold harmless ScamVanguard, its creator, and any affiliates from any claims, damages, or expenses arising from your use of the service or violation of these terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Changes to Terms</h2>
            <p className="text-gray-600">
              We may update these terms from time to time. We&apos;ll notify users of significant changes by posting a notice on our website. Continued use of the service after changes constitutes acceptance of the new terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Termination</h2>
            <p className="text-gray-600">
              We reserve the right to suspend or terminate access to the service for any user who violates these terms or uses the service inappropriately. Users may stop using the service at any time.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Governing Law</h2>
            <p className="text-gray-600">
              These terms are governed by the laws of the United States and the State of Texas, without regard to conflict of law principles.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">13. Contact Information</h2>
            <p className="text-gray-600">
              If you have questions about these terms, please contact us at:
            </p>
            <p className="mt-2">
              <a href="mailto:legal@scamvanguard.com" className="text-blue-600 hover:underline">
                legal@scamvanguard.com
              </a>
            </p>
          </section>

          <div className="bg-gray-50 rounded-lg p-6 mt-8">
            <p className="text-gray-600 text-sm">
              By using ScamVanguard, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer/>
    </div>
  );
}