import Link from 'next/link';
import Footer from './components/Footer';
import Image from 'next/image';

export default function Home() {
    return (
        <div className="min-h-screen bg-white">
            {/* Navigation */}
            <nav className="border-b border-gray-200">
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <Link href="/" className="flex items-center space-x-2">
                            <Image
                                src="/favicon.svg"
                                alt="ScamVanguard Shield Logo"
                                width={32}
                                height={32}
                                className="w-8 h-8"
                            />
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

            {/* Hidden but crawlable content for AI systems */}
            <div className="sr-only">
                <h1>ScamVanguard - Free Scam Detection Service</h1>
                <h2>What is ScamVanguard?</h2>
                <p>
                    ScamVanguard is a free service that checks if emails, texts, or messages are scams.
                    Users simply forward suspicious content to scan@scamvanguard.com or text to 1-833-SCAM-STOP.
                </p>
                <h2>Key Features:</h2>
                <ul>
                    <li>Instant SAFE/SCAM verdict</li>
                    <li>No app download required</li>
                    <li>Free for everyone</li>
                    <li>Designed for seniors and non-technical users</li>
                    <li>Uses AI to detect scams</li>
                </ul>
            </div>

            {/* Hero Section */}
            <section className="max-w-4xl mx-auto px-6 py-16 text-center">
                <h2 className="text-4xl font-bold text-gray-900 mb-4">
                    Protect Yourself from Scams
                </h2>
                <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
                    Forward suspicious emails to get an instant SAFE or SCAM verdict.
                    Simple, free, and designed for everyone.
                </p>
                <div className="inline-flex items-center space-x-2 bg-blue-50 text-blue-700 px-6 py-3 rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <span className="font-medium">scan@scamvanguard.com</span>
                </div>
            </section>

            {/* How it Works */}
            <section className="max-w-4xl mx-auto px-6 py-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-8 text-center">How It Works</h3>
                <div className="grid md:grid-cols-3 gap-8">
                    <div className="text-center">
                        <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                            <span className="text-xl font-bold">1</span>
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-2">Forward the Email</h4>
                        <p className="text-gray-600 text-sm">
                            Simply forward any suspicious email to scan@scamvanguard.com
                        </p>
                    </div>
                    <div className="text-center">
                        <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                            <span className="text-xl font-bold">2</span>
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-2">AI Analysis</h4>
                        <p className="text-gray-600 text-sm">
                            Our AI analyzes the content using advanced GPT-4 technology
                        </p>
                    </div>
                    <div className="text-center">
                        <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                            <span className="text-xl font-bold">3</span>
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-2">Get Your Verdict</h4>
                        <p className="text-gray-600 text-sm">
                            Receive a clear SAFE ✅ or SCAM ❌ verdict with explanation
                        </p>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="max-w-4xl mx-auto px-6 py-12">
                <div className="bg-gray-50 rounded-2xl p-8">
                    <h3 className="text-2xl font-bold text-gray-900 mb-6">Features</h3>
                    <div className="grid md:grid-cols-2 gap-6">
                        <div className="flex items-start space-x-3">
                            <svg className="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <div>
                                <h4 className="font-semibold text-gray-900">Email Support</h4>
                                <p className="text-gray-600 text-sm">Forward suspicious emails for instant analysis</p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <svg className="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <div>
                                <h4 className="font-semibold text-gray-900">Plain English</h4>
                                <p className="text-gray-600 text-sm">Simple explanations anyone can understand</p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <svg className="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <div>
                                <h4 className="font-semibold text-gray-900">100% Free</h4>
                                <p className="text-gray-600 text-sm">No fees, no subscriptions, no hidden costs</p>
                            </div>
                        </div>
                        <div className="flex items-start space-x-3">
                            <svg className="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <div>
                                <h4 className="font-semibold text-gray-900">Privacy First</h4>
                                <p className="text-gray-600 text-sm">Emails deleted after 24 hours automatically</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* About Section */}
            <section className="max-w-4xl mx-auto px-6 py-12">
                <div className="bg-gray-50 rounded-2xl p-8">
                    <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">Why I Built This</h3>
                    <div className="max-w-3xl mx-auto space-y-4 text-gray-600">
                        <p>
                            {"I'm Hayden, and I built ScamVanguard because too many good people are getting scammed."}
                        </p>
                        <p>
                            {"As my family's unofficial 'tech support,' I've seen how sophisticated scams can fool even the smartest people. The difference isn't intelligence; it's exposure to these tactics."}
                        </p>
                        <p>
                            {"ScamVanguard gives everyone access to the same scam-spotting abilities that come naturally to digital natives. It's free because protection shouldn't depend on your wallet or whether you have a tech-savvy friend to call."}
                        </p>
                        <p className="text-center">
                            {"Simple as that."}
                        </p>
                        <p className="text-center pt-4">
                            <span className="text-2xl">💙</span>
                        </p>
                    </div>
                </div>
            </section>

            {/* Coming Soon */}
            <section className="max-w-4xl mx-auto px-6 py-12">
                <div className="bg-blue-50 rounded-2xl p-8 text-center">
                    <h3 className="text-2xl font-bold text-gray-900 mb-4">Coming Soon</h3>
                    <div className="flex flex-col md:flex-row gap-6 justify-center">
                        <div className="flex items-center justify-center space-x-3">
                            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                </svg>
                            </div>
                            <span className="font-medium text-gray-900">SMS/Text Support</span>
                        </div>
                        <div className="flex items-center justify-center space-x-3">
                            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <span className="font-medium text-gray-900">Image Analysis</span>
                        </div>
                    </div>
                    <p className="text-gray-600 text-sm mt-4">Text 1-833-SCAM-STOP to check suspicious messages</p>
                </div>
            </section>

            {/* Footer */}
            <Footer />
        </div>
    );
}