import React from 'react';
import { Link } from 'react-router-dom';
import { 
    Accordion, 
    AccordionItem, 
    AccordionTrigger, 
    AccordionContent 
} from './components/ui/accordion';

export default function Learn() {
    return (
        <div className="min-h-screen bg-brutal-bg dark:bg-[#1A1D21] py-8 px-4 md:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-10">
                    <Link
                        to="/analyze"
                        className="inline-flex items-center gap-2 text-brutal-black dark:text-[#B9BBBE] hover:text-brutal-blue dark:hover:text-[#5865F2] mb-4 font-bold transition-colors"
                    >
                        ← Back to Analyzer
                    </Link>

                    <div className="card-brutal bg-gradient-to-r from-brutal-yellow to-brutal-green dark:from-[#2C2F33] dark:to-[#1E2124] p-6 md:p-8 border-3 border-brutal-black dark:border-[#43474D]">
                        <div className="flex flex-col md:flex-row items-center md:items-start gap-4 md:gap-6">
                            <div className="text-5xl md:text-6xl shrink-0">📚</div>
                            <div className="text-center md:text-left">
                                <h1 className="text-3xl md:text-4xl lg:text-5xl font-black font-mono mb-2 dark:text-white break-words">
                                    SECURITY ACADEMY
                                </h1>
                                <p className="text-base md:text-lg text-brutal-black/80 dark:text-[#B9BBBE]">
                                    Learn what every security check means - explained simply for everyone
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Info Section */}
                <div className="card-brutal bg-white dark:bg-[#242629] p-6 md:p-8 mb-10">
                    <h2 className="text-xl md:text-2xl font-black font-mono mb-6 dark:text-white">How to Use This Page</h2>
                    <div className="space-y-4 text-sm md:text-base text-brutal-black/80 dark:text-[#B9BBBE]">
                        <p className="flex items-start gap-3">
                            <span className="text-2xl">👆</span>
                            <span><strong className="dark:text-white">Click any section</strong> to expand and see detailed explanations</span>
                        </p>
                        <p className="flex items-start gap-3">
                            <span className="text-2xl">📖</span>
                            <span>Each section shows <strong className="dark:text-white">what it is, why it matters, and a real-world analogy</strong></span>
                        </p>
                        <p className="flex items-start gap-3">
                            <span className="text-2xl">✅</span>
                            <span><span className="inline-block px-2 py-1 bg-brutal-green dark:bg-[#00D9A3] dark:text-[#1A1D21] font-bold text-xs mr-1">Green badges</span> = Good security, <span className="inline-block px-2 py-1 bg-brutal-red/30 dark:bg-[#ED4245]/30 text-brutal-red dark:text-[#ED4245] font-bold text-xs mr-1">Red badges</span> = Needs attention</span>
                        </p>
                        <p className="flex items-start gap-3">
                            <span className="text-2xl">💡</span>
                            <span>Written in <strong className="dark:text-white">super simple language</strong> - no tech jargon!</span>
                        </p>
                    </div>
                </div>

                {/* FAQ Section with Accordion */}
                <div className="mb-10">
                    <div className="card-brutal bg-gradient-to-br from-brutal-blue/20 to-brutal-green/20 dark:from-[#2C2F33] dark:to-[#1E2124] p-6 md:p-8 mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="text-3xl md:text-4xl">❓</span>
                            <h2 className="text-xl md:text-2xl lg:text-3xl font-black font-mono dark:text-white">
                                Frequently Asked Questions
                            </h2>
                        </div>
                        <p className="text-sm md:text-base text-brutal-black/70 dark:text-[#8E9297]">
                            Quick answers to common questions about website security
                        </p>
                    </div>

                    <Accordion type="single" collapsible className="w-full">
                        <AccordionItem value="item-1">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🔒</span>
                                    <span className="text-base md:text-lg">What is website security and why does it matter?</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-3">
                                    <p>
                                        Website security is like having locks, alarms, and security cameras for your online presence. 
                                        It protects your website and its visitors from hackers, data thieves, and malicious attacks.
                                    </p>
                                    <p className="font-bold text-brutal-black dark:text-white">Why it matters:</p>
                                    <ul className="list-disc list-inside space-y-2 ml-4">
                                        <li><strong>Protects user data</strong> - Keeps passwords, personal info, and payment details safe</li>
                                        <li><strong>Builds trust</strong> - Visitors feel confident using your site</li>
                                        <li><strong>Prevents attacks</strong> - Stops hackers from stealing or damaging data</li>
                                        <li><strong>Improves SEO</strong> - Google ranks secure sites higher</li>
                                        <li><strong>Legal compliance</strong> - Meets GDPR and other regulations</li>
                                    </ul>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="item-2">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🛡️</span>
                                    <span className="text-base md:text-lg">What are HTTP Security Headers?</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-3">
                                    <p>
                                        HTTP Security Headers are invisible instructions your website sends to browsers, telling them how to handle your content safely. 
                                        Think of them as rules that protect visitors from common attacks.
                                    </p>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">🎯 Key Security Headers:</p>
                                        <ul className="list-disc list-inside space-y-1 text-sm">
                                            <li><strong>HSTS</strong> - Forces encrypted connections only</li>
                                            <li><strong>CSP</strong> - Blocks unauthorized scripts and resources</li>
                                            <li><strong>X-Frame-Options</strong> - Prevents clickjacking attacks</li>
                                            <li><strong>X-Content-Type-Options</strong> - Stops MIME type sniffing</li>
                                            <li><strong>Referrer-Policy</strong> - Controls what info is shared</li>
                                        </ul>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="item-3">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🔐</span>
                                    <span className="text-base md:text-lg">How do I know if my website is secure?</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-3">
                                    <p>
                                        Use our Site Security Analyzer tool to get a comprehensive security check! Here's what to look for:
                                    </p>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        <div className="p-3 bg-brutal-green/20 dark:bg-[#00D9A3]/10 border-2 border-brutal-green dark:border-[#00D9A3] rounded-sm">
                                            <p className="font-bold mb-2 dark:text-white">✅ Good Signs:</p>
                                            <ul className="list-disc list-inside space-y-1 text-sm">
                                                <li>HTTPS lock icon in browser</li>
                                                <li>Valid SSL certificate</li>
                                                <li>Security headers present</li>
                                                <li>No mixed content warnings</li>
                                                <li>Regular security updates</li>
                                            </ul>
                                        </div>
                                        <div className="p-3 bg-brutal-red/20 dark:bg-[#ED4245]/10 border-2 border-brutal-red dark:border-[#ED4245] rounded-sm">
                                            <p className="font-bold mb-2 dark:text-white">⚠️ Warning Signs:</p>
                                            <ul className="list-disc list-inside space-y-1 text-sm">
                                                <li>"Not Secure" in address bar</li>
                                                <li>Expired SSL certificate</li>
                                                <li>Missing security headers</li>
                                                <li>Outdated software versions</li>
                                                <li>Browser security warnings</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="item-4">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">⚡</span>
                                    <span className="text-base md:text-lg">What's the difference between HTTP and HTTPS?</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-3">
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">🔴 HTTP (Not Secure)</p>
                                        <p className="text-sm">
                                            Data travels in plain text - like sending a postcard. Anyone along the route can read your messages, 
                                            passwords, and personal information. <strong className="dark:text-white">Never use for sensitive data!</strong>
                                        </p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-green dark:border-[#00D9A3] rounded-sm">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">🟢 HTTPS (Secure)</p>
                                        <p className="text-sm">
                                            Data is encrypted - like putting your postcard in a locked safe. Only the sender and receiver can read it. 
                                            <strong className="dark:text-white"> This is the standard for all modern websites.</strong>
                                        </p>
                                    </div>
                                    <p className="text-sm italic">
                                        💡 <strong className="dark:text-white">Pro Tip:</strong> Always look for the padlock icon 🔒 in your browser's address bar before entering sensitive information!
                                    </p>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="item-5">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🚀</span>
                                    <span className="text-base md:text-lg">How can I improve my website's security score?</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <p>Here's a step-by-step checklist to boost your security:</p>
                                    
                                    <div className="space-y-3">
                                        <div className="p-3 bg-white dark:bg-[#1E2124] border-l-4 border-brutal-blue dark:border-[#5865F2]">
                                            <p className="font-bold text-brutal-blue dark:text-[#5865F2] mb-1">1. Enable HTTPS</p>
                                            <p className="text-sm">Get a free SSL certificate from Let's Encrypt or your hosting provider</p>
                                        </div>
                                        
                                        <div className="p-3 bg-white dark:bg-[#1E2124] border-l-4 border-brutal-blue dark:border-[#5865F2]">
                                            <p className="font-bold text-brutal-blue dark:text-[#5865F2] mb-1">2. Add Security Headers</p>
                                            <p className="text-sm">Configure your server to send security headers (check our sections below!)</p>
                                        </div>
                                        
                                        <div className="p-3 bg-white dark:bg-[#1E2124] border-l-4 border-brutal-blue dark:border-[#5865F2]">
                                            <p className="font-bold text-brutal-blue dark:text-[#5865F2] mb-1">3. Keep Software Updated</p>
                                            <p className="text-sm">Regular updates patch security vulnerabilities</p>
                                        </div>
                                        
                                        <div className="p-3 bg-white dark:bg-[#1E2124] border-l-4 border-brutal-blue dark:border-[#5865F2]">
                                            <p className="font-bold text-brutal-blue dark:text-[#5865F2] mb-1">4. Use Strong Authentication</p>
                                            <p className="text-sm">Implement 2FA and enforce strong password policies</p>
                                        </div>
                                        
                                        <div className="p-3 bg-white dark:bg-[#1E2124] border-l-4 border-brutal-blue dark:border-[#5865F2]">
                                            <p className="font-bold text-brutal-blue dark:text-[#5865F2] mb-1">5. Regular Security Scans</p>
                                            <p className="text-sm">Use tools like ours to monitor your security posture continuously</p>
                                        </div>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="item-6">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">📧</span>
                                    <span className="text-base md:text-lg">What are SPF and DMARC for email security?</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-3">
                                    <p>
                                        SPF and DMARC are email authentication protocols that prevent spammers and scammers from 
                                        sending emails pretending to be from your domain.
                                    </p>
                                    
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📮 SPF (Sender Policy Framework)</p>
                                        <p className="text-sm">
                                            Creates a list of servers allowed to send emails for your domain. Like a guest list 
                                            at an exclusive party - if you're not on the list, you can't send emails as that domain.
                                        </p>
                                    </div>
                                    
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">🛡️ DMARC (Domain-based Message Authentication)</p>
                                        <p className="text-sm">
                                            Tells other email servers what to do with emails that fail SPF checks - quarantine, reject, or allow them. 
                                            Also provides reports on who's trying to use your domain.
                                        </p>
                                    </div>
                                    
                                    <p className="text-sm italic">
                                        💡 <strong className="dark:text-white">Why this matters:</strong> Protects your domain reputation and prevents phishing attacks using your brand name.
                                    </p>
                                </div>
                            </AccordionContent>
                        </AccordionItem>
                    </Accordion>
                </div>

                {/* Security Concepts - All Explained */}
                <div className="mb-10">
                    <div className="card-brutal bg-gradient-to-br from-brutal-green/20 to-brutal-yellow/20 dark:from-[#2C2F33] dark:to-[#1E2124] p-6 md:p-8 mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="text-3xl md:text-4xl">🔐</span>
                            <h2 className="text-xl md:text-2xl lg:text-3xl font-black font-mono dark:text-white">
                                Security Features Explained
                            </h2>
                        </div>
                        <p className="text-sm md:text-base text-brutal-black/70 dark:text-[#8E9297]">
                            Every security check explained in simple words - click to expand and learn
                        </p>
                    </div>

                    <Accordion type="single" collapsible className="w-full">
                        <AccordionItem value="https">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🔒</span>
                                    <span className="text-base md:text-lg font-black">HTTPS - Secure Connection</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">Website uses HTTPS - Your data is encrypted and safe</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">Website uses HTTP - Your data can be read by anyone!</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">Think of HTTPS like sending a letter in a locked box instead of an open postcard. When you visit a website with HTTPS, all your information (like passwords, credit cards) travels in a secret code that hackers can't read.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Without HTTPS, anyone spying on the internet can see EVERYTHING you type - passwords, messages, bank details. It's like shouting your secrets in a crowded room.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">It's like the difference between whispering a secret and shouting it in public.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="hsts">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🛡️</span>
                                    <span className="text-base md:text-lg font-black">HSTS - Always Use Secure Connection</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">HSTS enabled - Browser will always use secure connection</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">HSTS missing - Hackers could trick you into using unsafe connection</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">HSTS is like a promise from the website saying 'I will ALWAYS use the locked box (HTTPS), never send open postcards (HTTP)'. Your browser remembers this promise and won't let you accidentally use the unsafe version.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Sometimes hackers try to trick you into using the unsafe version (HTTP) to steal your data. HSTS stops this trick from working.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like a restaurant that promises to always wash their hands - once they promise, you know they'll do it every time.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="csp">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🚫</span>
                                    <span className="text-base md:text-lg font-black">CSP - Content Security Policy</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">CSP present - Website controls what code can run</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">CSP missing - Anyone could inject harmful code</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">CSP is like a bouncer at a club who checks everyone's ID. It tells the browser: 'only load stuff (images, scripts) from these trusted places'. This stops bad guys from sneaking in harmful code.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Hackers try to inject bad code into websites (like viruses). CSP is a filter that blocks anything that doesn't come from approved sources.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like having a security guard who only lets people on the guest list into your party.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="x_frame">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🖼️</span>
                                    <span className="text-base md:text-lg font-black">X-Frame-Options - Prevent Fake Copies</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">X-Frame-Options set - Can't be put in fake frames</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">X-Frame-Options missing - Could be framed by scammers</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">This stops bad guys from putting the real website inside a fake frame - like putting a real store window inside a fake building. They could trick you into thinking you're on the real site when you're not.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Scammers create fake websites that look exactly like the real one (like your bank). Without X-Frame-Options, they can trap the real site inside their fake site to steal your password.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like a store that won't let anyone take photos of their displays to make fake copies.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="x_content">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">📄</span>
                                    <span className="text-base md:text-lg font-black">X-Content-Type-Options - File Type Safety</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">Protection enabled - Files must be what they claim</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">Protection missing - Dangerous files could pretend to be safe</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">This tells the browser: 'A picture is a picture, a text file is a text file - don't let them pretend to be something else'. It stops hackers from disguising dangerous files as safe ones.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Hackers can hide virus code inside what looks like a harmless image. This setting makes the browser check what the file REALLY is, not just what it claims to be.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like airport security that actually checks what's in your bag, not just what the label says.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="referrer">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🔍</span>
                                    <span className="text-base md:text-lg font-black">Referrer Policy - Privacy Protection</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">Policy set - Controls what information is shared</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">Policy missing - Full browsing history could leak</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">When you click a link, websites can see where you came from (like breadcrumbs). Referrer Policy controls how much of this information is shared. It's like choosing whether to tell people your full address or just your city.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Without this, other websites could track your journey across the internet - seeing every page you visited before. It's a privacy issue.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like choosing to introduce yourself with just your first name instead of your full name and address.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="permissions">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🎤</span>
                                    <span className="text-base md:text-lg font-black">Permissions Policy - Control Website Powers</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">Policy set - Website limits its own powers</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">Policy missing - Website could request any permission</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">This is like permission slips for websites. It controls whether the website can use your camera, microphone, location, etc. The website tells the browser: 'I only need these specific powers'.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Bad websites could try to secretly turn on your camera or track your location. This policy limits what powers websites have.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like a babysitter agreeing to only use the kitchen and living room, not go through your bedroom.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="spf">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">📧</span>
                                    <span className="text-base md:text-lg font-black">SPF - Email Authentication</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">SPF record found - Emails can be verified as authentic</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">SPF missing - Easy to fake emails from this domain</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">SPF is like a signature that proves emails really come from who they say they're from. It's a list of computers allowed to send emails for this domain.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Scammers send fake emails pretending to be from your bank or favorite stores. SPF helps email services detect these fakes.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like having an official stamp on a letter to prove it's really from the government, not a scammer.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="dmarc">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🛡️</span>
                                    <span className="text-base md:text-lg font-black">DMARC - Email Protection Policy</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ When Present:</p>
                                        <p className="text-sm">DMARC found - Strong email security policy in place</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Missing:</p>
                                        <p className="text-sm">DMARC missing - Weak protection against email scams</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">DMARC is the boss of email security. It tells email services: 'If someone sends a fake email pretending to be me, throw it in the trash or mark it as spam'. It's an extra layer on top of SPF.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">Even with SPF, scammers try to fake emails. DMARC gives clear instructions on what to do with suspicious emails.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like having a security system that not only detects intruders but also calls the police automatically.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>

                        <AccordionItem value="server">
                            <AccordionTrigger>
                                <span className="flex items-center gap-3">
                                    <span className="text-xl md:text-2xl">🏷️</span>
                                    <span className="text-base md:text-lg font-black">Server Header - Information Leak</span>
                                </span>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-4">
                                    <div className="p-4 bg-brutal-green/10 dark:bg-[#00D9A3]/10 border-l-4 border-brutal-green dark:border-[#00D9A3]">
                                        <p className="font-bold mb-2 text-brutal-green dark:text-[#00D9A3]">✅ Best Practice:</p>
                                        <p className="text-sm">Server info hidden - Hackers have to guess</p>
                                    </div>
                                    <div className="p-4 bg-brutal-red/10 dark:bg-[#ED4245]/10 border-l-4 border-brutal-red dark:border-[#ED4245]">
                                        <p className="font-bold mb-2 text-brutal-red dark:text-[#ED4245]">⚠️ When Exposed:</p>
                                        <p className="text-sm">Server info exposed - Hackers know exactly what to attack</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">📖 Simple Explanation:</p>
                                        <p className="text-sm">The server header is like a name tag that tells everyone what software is running the website. While not dangerous by itself, it's like telling burglars exactly what kind of locks you have on your doors.</p>
                                    </div>
                                    <div className="p-4 bg-white dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">❓ Why Does This Matter?</p>
                                        <p className="text-sm">If hackers know your exact server software version, they can look up known vulnerabilities (weaknesses) and attack them. It's giving them a cheat sheet.</p>
                                    </div>
                                    <div className="p-4 bg-brutal-yellow/20 dark:bg-[#2C2F33] border-2 border-brutal-black dark:border-[#43474D] rounded-sm">
                                        <p className="font-bold mb-2 dark:text-white">💡 Think of it like this:</p>
                                        <p className="text-sm italic">Like not telling strangers what kind of alarm system you have at home.</p>
                                    </div>
                                </div>
                            </AccordionContent>
                        </AccordionItem>
                    </Accordion>
                </div>

                {/* Bottom CTA */}
                <div className="card-brutal bg-brutal-blue/20 dark:bg-[#5865F2]/10 border-3 border-brutal-blue dark:border-[#5865F2] p-6 md:p-10 text-center">
                    <h3 className="text-xl md:text-2xl lg:text-3xl font-black font-mono mb-4 dark:text-white">Ready to Test Your Knowledge?</h3>
                    <p className="mb-8 text-sm md:text-base text-brutal-black/80 dark:text-[#B9BBBE] max-w-2xl mx-auto">
                        Scan your own website and see which security features it has!
                    </p>
                    <Link
                        to="/analyze"
                        className="inline-block btn-brutal bg-brutal-black dark:bg-[#5865F2] text-white px-8 md:px-12 py-4 text-base md:text-lg shadow-brutal-lg font-bold hover:translate-x-1 hover:translate-y-1 transition-all"
                    >
                        Start Scanning →
                    </Link>
                </div>
            </div>
        </div>
    );
}
