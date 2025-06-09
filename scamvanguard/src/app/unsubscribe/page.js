import Link from 'next/link';
import Footer from './components/Footer';

export default function Unsubscribe() {
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
            <div className="flex items-center space-x-6">
              <Link href="/how-it-works" className="text-md font-medium text-gray-600 hover:text-gray-900 transition-colors">
                How It Works
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
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Stop Using ScamVanguard</h1>
        
        <div className="bg-blue-50 border-l-4 border-blue-600 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">No Unsubscribe Needed!</h2>
          <p className="text-gray-700">
            ScamVanguard doesn&apos;t send any emails unless you forward something to us. To stop using the service, simply stop forwarding emails to scan@scamvanguard.com.
          </p>
        </div>

        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">How Our Service Works</h2>
          <div className="space-y-4">
            <p className="text-gray-600">
              ScamVanguard is an <strong>on-demand service</strong>. We only respond when you actively send us an email to check. Think of it like this:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>When you forward an email to us → We analyze it and send you a response</li>
              <li>When you don&apos;t forward anything → We don&apos;t contact you at all</li>
            </ul>
            <p className="text-gray-600 mt-4">
              There&apos;s no mailing list, no newsletters, and no automated messages. You&apos;re in complete control.
            </p>
          </div>
        </section>

        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Frequently Asked Questions</h2>
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-medium text-gray-900 mb-2">Do I need to unsubscribe?</h3>
              <p className="text-gray-600">
                No! There&apos;s nothing to unsubscribe from. We don&apos;t maintain a mailing list or send any unsolicited emails. We only respond to emails you send us.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-medium text-gray-900 mb-2">Will you keep my email address?</h3>
              <p className="text-gray-600">
                Your email and any forwarded content are automatically deleted from our systems after 24 hours. We don&apos;t store email addresses or maintain user accounts.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-medium text-gray-900 mb-2">What if I accidentally forward something?</h3>
              <p className="text-gray-600">
                No problem! You&apos;ll receive one analysis response for that email, and then nothing else. Your data will be deleted after 24 hours as usual.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-medium text-gray-900 mb-2">Can I use the service again later?</h3>
              <p className="text-gray-600">
                Absolutely! The service is always available. Simply forward a suspicious email to scan@scamvanguard.com anytime you need help.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-medium text-gray-900 mb-2">What if I keep getting responses I didn&apos;t ask for?</h3>
              <p className="text-gray-600">
                This shouldn&apos;t happen since we only respond to emails you forward. If you&apos;re receiving unexpected emails from us, please contact us at privacy@scamvanguard.com so we can investigate.
              </p>
            </div>
          </div>
        </section>

        <section className="mb-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Still Want to Block Our Emails?</h2>
          <p className="text-gray-600 mb-4">
            If you want to ensure you never receive responses from ScamVanguard (even if you accidentally forward something), you can:
          </p>
          <ul className="list-disc pl-6 space-y-2 text-gray-600">
            <li>Add <span className="font-mono bg-gray-100 px-2 py-1 rounded">noreply@scamvanguard.com</span> to your email&apos;s block list</li>
            <li>Create a filter in your email client to automatically delete emails from our domain</li>
            <li>Mark any response as spam (though we&apos;d prefer you didn&apos;t, as it affects our ability to help others)</li>
          </ul>
        </section>

        <section>
          <div className="bg-gray-50 rounded-2xl p-8 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Remember</h2>
            <p className="text-gray-600 mb-6">
              You&apos;re always in control. Use ScamVanguard when you need it, ignore it when you don&apos;t.
            </p>
            <p className="text-gray-600">
              Questions? Contact us at{' '}
              <a href="mailto:privacy@scamvanguard.com" className="text-blue-600 hover:underline">
                contact@scamvanguard.com
              </a>
            </p>
          </div>
        </section>
      </div>

      {/* Footer */}
      <Footer/>
    </div>
  );
}