import Link from 'next/link';
import Footer from '../components/Footer';

export default function HowItWorks() {
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

      {/* Hero Section */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">How ScamVanguard Works</h1>
        <p className="text-xl text-gray-600">
          Learn how our AI-powered service protects you from scams in three simple steps.
        </p>
      </section>

      {/* Detailed Process */}
      <section className="max-w-4xl mx-auto px-6 py-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-8">The Process Explained</h2>
        
        <div className="space-y-8">
          <div className="flex gap-6">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                1
              </div>
            </div>
            <div className="flex-grow">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">You Forward the Suspicious Email</h3>
              <p className="text-gray-600 mb-4">
                Simply forward any email you&apos;re unsure about to <span className="font-mono bg-gray-100 px-2 py-1 rounded">scan@scamvanguard.com</span>. 
                You don&apos;t need to add any message - just forward it as-is.
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 font-medium mb-2">Pro tip:</p>
                <p className="text-sm text-gray-600">
                  Include the original email headers by forwarding (not copy-pasting) for the most accurate analysis.
                </p>
              </div>
            </div>
          </div>

          <div className="flex gap-6">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                2
              </div>
            </div>
            <div className="flex-grow">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Our AI Analyzes the Content</h3>
              <p className="text-gray-600 mb-4">
                Within seconds, our advanced AI (powered by GPT-4) examines multiple factors:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600">
                <li>Sender authenticity and email headers</li>
                <li>Language patterns common in scams</li>
                <li>Urgent or threatening messaging</li>
                <li>Suspicious links and attachments</li>
                <li>Requests for personal information or money</li>
                <li>Grammar and spelling inconsistencies</li>
                <li>Impersonation attempts</li>
              </ul>
            </div>
          </div>

          <div className="flex gap-6">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                3
              </div>
            </div>
            <div className="flex-grow">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">You Receive a Clear Verdict</h3>
              <p className="text-gray-600 mb-4">
                Within minutes, you&apos;ll receive an email response with one of three verdicts:
              </p>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✅</span>
                  <div>
                    <p className="font-semibold text-gray-900">SAFE</p>
                    <p className="text-sm text-gray-600">The email appears legitimate with no scam indicators detected.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-2xl">❌</span>
                  <div>
                    <p className="font-semibold text-gray-900">SCAM</p>
                    <p className="text-sm text-gray-600">Clear scam indicators found. Do not interact with the sender.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div>
                    <p className="font-semibold text-gray-900">UNSURE</p>
                    <p className="text-sm text-gray-600">Mixed signals detected. Exercise caution and verify independently.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Example Section */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-semibold text-gray-900 mb-8">Example Emails and Responses</h2>
        
        <div className="space-y-6">
          {/* Scam Example */}
          <div className="bg-red-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-xl">❌</span> Example: Classic Phishing Scam
            </h3>
            <div className="bg-white rounded p-4 mb-4 text-sm font-mono text-gray-700">
              <p className="mb-2">From: security@amaz0n-verify.com</p>
              <p className="mb-2">Subject: Urgent: Your Account Will Be Closed!</p>
              <p>Dear Customer,</p>
              <p>Your Amazon account has suspicious activity. Click here immediately to verify or your account will be deleted in 24 hours!</p>
            </div>
            <div className="bg-white rounded p-4">
              <p className="font-semibold text-gray-900 mb-2">Our Response:</p>
              <p className="text-gray-700">
                <span className="font-semibold">❌ SCAM</span> - This email shows multiple scam indicators: fake sender domain (amaz0n-verify.com), urgent threats, and requests to click suspicious links. Amazon never threatens immediate account closure via email. Delete this message.
              </p>
            </div>
          </div>

          {/* Safe Example */}
          <div className="bg-green-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-xl">✅</span> Example: Legitimate Business Email
            </h3>
            <div className="bg-white rounded p-4 mb-4 text-sm font-mono text-gray-700">
              <p className="mb-2">From: noreply@email.apple.com</p>
              <p className="mb-2">Subject: Your receipt from Apple</p>
              <p>Apple Receipt</p>
              <p>Thank you for your purchase of iCloud+ for $0.99. This email confirms your monthly subscription renewal.</p>
            </div>
            <div className="bg-white rounded p-4">
              <p className="font-semibold text-gray-900 mb-2">Our Response:</p>
              <p className="text-gray-700">
                <span className="font-semibold">✅ SAFE</span> - This appears to be a legitimate receipt from Apple. The sender domain is correct, the message matches standard Apple formatting, and it&apos;s confirming a regular subscription charge. If you have this subscription, this email is genuine.
              </p>
            </div>
          </div>

          {/* Unsure Example */}
          <div className="bg-yellow-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-xl">⚠️</span> Example: Unclear Intent
            </h3>
            <div className="bg-white rounded p-4 mb-4 text-sm font-mono text-gray-700">
              <p className="mb-2">From: john.smith@gmail.com</p>
              <p className="mb-2">Subject: Investment Opportunity</p>
              <p>Hi,</p>
              <p>I found your contact online. I have a business proposal that could interest you. Can we discuss?</p>
            </div>
            <div className="bg-white rounded p-4">
              <p className="font-semibold text-gray-900 mb-2">Our Response:</p>
              <p className="text-gray-700">
                <span className="font-semibold">⚠️ UNSURE</span> - This email could be legitimate or a scam. While it doesn&apos;t contain obvious scam indicators, unsolicited investment offers are often fraudulent. If you don&apos;t know this person, it&apos;s best to ignore. Never send money to unknown contacts.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Types of Scams */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-semibold text-gray-900 mb-8">Types of Scams We Detect</h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Phishing Scams</h3>
            <p className="text-gray-600 text-sm mb-3">
              Fake emails pretending to be from legitimate companies to steal your login credentials or personal information.
            </p>
            <p className="text-sm text-gray-500">
              <strong>Common signs:</strong> Suspicious sender addresses, urgent language, requests for passwords
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Advance Fee Fraud</h3>
            <p className="text-gray-600 text-sm mb-3">
              Promises of large sums of money in exchange for a small upfront payment or &quot;processing fee.&quot;
            </p>
            <p className="text-sm text-gray-500">
              <strong>Common signs:</strong> Nigerian prince emails, lottery winnings, inheritance claims
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Romance Scams</h3>
            <p className="text-gray-600 text-sm mb-3">
              Fake romantic interests who build trust before asking for money for emergencies or travel.
            </p>
            <p className="text-sm text-gray-500">
              <strong>Common signs:</strong> Quick declarations of love, sob stories, requests for money
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Tech Support Scams</h3>
            <p className="text-gray-600 text-sm mb-3">
              Claims that your computer is infected or your account is compromised, offering fake support.
            </p>
            <p className="text-sm text-gray-500">
              <strong>Common signs:</strong> Unsolicited contact, requests for remote access, payment demands
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Job Scams</h3>
            <p className="text-gray-600 text-sm mb-3">
              Fake job offers that require upfront payments or personal information before &quot;hiring.&quot;
            </p>
            <p className="text-sm text-gray-500">
              <strong>Common signs:</strong> Too-good-to-be-true salaries, vague job descriptions, upfront fees
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Government Impersonation</h3>
            <p className="text-gray-600 text-sm mb-3">
              Fake messages claiming to be from the IRS, Social Security, or other government agencies.
            </p>
            <p className="text-sm text-gray-500">
              <strong>Common signs:</strong> Threats of arrest, demands for immediate payment, gift card requests
            </p>
          </div>
        </div>
      </section>

      {/* Accuracy Information */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-semibold text-gray-900 mb-8">Accuracy and Limitations</h2>
        
        <div className="bg-blue-50 rounded-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">How Accurate Is ScamVanguard?</h3>
          <p className="text-gray-700 mb-4">
            Our AI-powered analysis is highly effective at detecting common scam patterns and has been trained on thousands of examples. However, like all AI systems, it&apos;s not perfect.
          </p>
          <div className="space-y-2">
            <p className="text-gray-700">
              <strong>✅ Strengths:</strong> Excellent at detecting known scam patterns, phishing attempts, and common fraud tactics
            </p>
            <p className="text-gray-700">
              <strong>⚠️ Limitations:</strong> May miss brand new scam types, sophisticated targeted attacks, or context-specific fraud
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold text-gray-900">Important Reminders</h3>
          <ul className="space-y-2">
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-600">Always use ScamVanguard as one tool in your decision-making process, not your only source</p>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-600">When in doubt, independently verify by contacting companies directly through official channels</p>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-600">Trust your instincts - if something feels wrong, it probably is</p>
            </li>
            <li className="flex items-start gap-2">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-600">Never send money or personal information based solely on an email, even if we mark it as &quot;SAFE&quot;</p>
            </li>
          </ul>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-gray-50 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Ready to Check an Email?</h2>
          <p className="text-gray-600 mb-6">
            Forward any suspicious email to our scanning address:
          </p>
          <div className="inline-flex items-center space-x-2 bg-blue-50 text-blue-700 px-6 py-3 rounded-lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span className="font-medium">scan@scamvanguard.com</span>
          </div>
          <p className="text-sm text-gray-500 mt-4">
            No signup required • 100% free • Response in minutes
          </p>
        </div>
      </section>

      {/* Footer */}
      <Footer/>
    </div>
  );
}