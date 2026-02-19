import React, { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import DOMPurify from 'dompurify';
import api from "./api";

export default function SiteSecurityAnalyzer() {
  const [searchParams] = useSearchParams();
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [toast, setToast] = useState(null);
  // Progress % shown while async Celery scan is being polled
  const [scanProgress, setScanProgress] = useState(0);

  const showToast = (message, type = 'success') => {
    const sanitized = DOMPurify.sanitize(message, { ALLOWED_TAGS: [] });
    setToast({ message: sanitized, type });
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    const urlParam = searchParams.get('url');
    if (urlParam) {
      setUrl(DOMPurify.sanitize(urlParam, { ALLOWED_TAGS: [] }));
    }
  }, [searchParams]);

  /**
   * Poll /scan/status/<taskId> every 2 s until the Celery task finishes.
   * The backend returns { status: 'complete'|'failed'|'processing', result, progress }.
   */
  const pollScanStatus = async (taskId) => {
    const MAX_ATTEMPTS = 60; // 60 × 2 s = 120 s max (2 minutes for complex sites like YouTube)
    for (let i = 0; i < MAX_ATTEMPTS; i++) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const status = await api.get(`/scan/status/${taskId}`);

      if (status.status === 'complete') {
        setScanProgress(100);
        return status.result;
      }
      if (status.status === 'failed') {
        throw new Error(status.error || 'Scan failed on server side');
      }
      // Update progress bar using backend-reported progress or estimated progress
      const pct = status.progress || Math.round(((i + 1) / MAX_ATTEMPTS) * 90);
      setScanProgress(pct);
    }
    throw new Error('Scan timed out after 2 minutes. The site may be slow or unreachable.');
  };

  const handleScan = async () => {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      showToast('Please enter a URL', 'error');
      return;
    }

    setLoading(true);
    setResult(null);
    setShowDetails(false);
    setScanProgress(5);

    try {
      // POST /scan — backend returns 202 {task_id, status:"queued"} when Celery is running.
      // It may also return an immediate result if the domain was recently cached.
      const queued = await api.post('/scan', { url: trimmedUrl });

      let data;
      if (queued.task_id && queued.status === 'queued') {
        // Async path: poll for result
        setScanProgress(10);
        data = await pollScanStatus(queued.task_id);
      } else if (queued.report || queued.findings) {
        // Synchronous / cached result returned directly
        data = queued;
      } else {
        throw new Error(queued.message || 'Unexpected response from server');
      }

      if (data) {
        const sanitizedData = {
          ...data,
          explanation: DOMPurify.sanitize(data.explanation || '', {
            ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'br'],
            ALLOWED_ATTR: []
          }),
          // 'report' is the flat boolean map; fall back to 'findings.headers' for legacy responses
          report: data.report || data.findings?.headers || {}
        };
        setResult(sanitizedData);
        showToast('Scan complete!', 'success');
      }
    } catch (error) {
      const errorMsg = error.message || 'Failed to scan site.';
      setResult({ error: DOMPurify.sanitize(errorMsg, { ALLOWED_TAGS: [] }) });
      showToast(errorMsg, 'error');
    } finally {
      setLoading(false);
      setScanProgress(0);
    }
  };

  // Identical to computeScore in History.jsx — keep both in sync.
  const calculateScore = (report) => {
    if (!report) return 0;
    let score = 50;
    if (report.https) score += 15;
    if (report.hsts) score += 10;
    if (report.content_security_policy) score += 10;
    if (report.x_frame_options) score += 5;
    else score -= 5;
    if (report.x_content_type_options) score += 5;
    else score -= 5;
    if (report.referrer_policy) score += 5;
    else score -= 3;
    if (report.permissions_policy) score += 5;
    if (report.dns_spf) score += 5;
    if (report.dns_dmarc) score += 5;
    if (report.server_header) score -= 3;
    return Math.max(0, Math.min(100, Math.round(score)));
  };

  // Prefer pre-calculated backend score; fall back to client-side calculation
  const score = result?.score ?? (result?.report ? calculateScore(result.report) : 0);

  const scoreLabel = (s) => s >= 80 ? 'EXCELLENT' : s >= 60 ? 'GOOD' : s >= 40 ? 'MODERATE' : 'CRITICAL';
  const scoreBg = (s) => s >= 80 ? 'bg-green-500 text-black' : s >= 60 ? 'bg-blue-500 text-white' : s >= 40 ? 'bg-yellow-400 text-black' : 'bg-red-500 text-white';

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 p-4 md:p-8 font-sans text-gray-900 dark:text-gray-100">
      <div className="max-w-5xl mx-auto">
        {toast && (
          <div className={`fixed top-4 right-4 z-50 px-6 py-3 border-2 border-black dark:border-gray-600 shadow-md font-bold font-mono text-sm animate-slide-up ${
            toast.type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-black'
          }`}>
            {toast.message}
          </div>
        )}

        <main>
          <div className="flex flex-col md:flex-row gap-4 mb-12">
            <input
              type="text"
              className="flex-grow px-4 py-3 text-xl md:text-2xl font-mono border-2 border-black dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800"
              placeholder="ENTER URL (e.g. google.com)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleScan()}
              maxLength={2048}
            />
            <button
              onClick={handleScan}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-xl font-bold border-2 border-black dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors md:w-48 flex justify-center items-center"
            >
              {loading
                ? <span className="animate-pulse">{scanProgress > 0 ? `${scanProgress}%` : 'SCANNING...'}</span>
                : 'ANALYZE'}
            </button>
          </div>

          {result && (
            <div className="animate-slide-up w-full">
              <div className="max-w-full w-full px-2 md:px-4">
                {result.error ? (
                  <div className="bg-red-500 text-white p-4 border-2 border-black dark:border-gray-600">
                    <h2 className="text-xl md:text-2xl font-bold font-mono">ERROR</h2>
                    <p className="text-sm md:text-base">{result.error}</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6 w-full">
                    <div className="bg-white dark:bg-gray-800 border-2 border-black dark:border-gray-600 lg:col-span-1 flex flex-col items-center justify-center text-center p-4 md:p-6">
                      <h3 className="font-mono text-lg md:text-xl mb-4 border-b-2 border-black dark:border-gray-600 w-full pb-2">SECURITY SCORE</h3>
                      <div className={`w-32 h-32 md:w-40 md:h-40 rounded-full border-4 border-black dark:border-gray-600 flex items-center justify-center mb-4 shadow-md ${scoreBg(score)}`}>
                        <span className="text-4xl md:text-5xl font-bold font-mono">{score}%</span>
                      </div>
                      <div className="font-bold text-base md:text-lg">
                        {scoreLabel(score)}
                      </div>
                    </div>

                    <div className="lg:col-span-2 flex flex-col gap-4 md:gap-6 lg:gap-8">
                      <div className="bg-white dark:bg-gray-800 border-2 border-black dark:border-gray-600 p-4 md:p-6">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-4 border-b-2 border-black dark:border-gray-600 pb-3">
                          <h3 className="font-mono text-lg md:text-xl">ANALYSIS REPORT</h3>
                        </div>
                        <div className="p-3 md:p-4 bg-gray-50 dark:bg-gray-800 border-2 border-black dark:border-gray-600 mb-4 md:mb-6 font-mono text-xs md:text-sm break-words">
                          <div dangerouslySetInnerHTML={{ __html: result.explanation }} />
                        </div>
                        <Link
                          to="/learn"
                          className="block w-full bg-yellow-400 hover:bg-yellow-500 text-black border-2 border-black dark:border-gray-600 text-xs md:text-sm py-2 md:py-3 mb-3 md:mb-4 text-center font-bold transition-colors"
                        >
                          <span className="text-base md:text-xl">📚</span> LEARN WHAT THESE MEAN (SIMPLE LESSONS)
                        </Link>
                        <button
                          onClick={() => setShowDetails(!showDetails)}
                          className="w-full border-2 border-black dark:border-gray-600 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-xs md:text-sm py-2 mb-3 md:mb-4 transition-colors"
                        >
                          {showDetails ? "HIDE TECHNICAL DATA" : "SHOW TECHNICAL DATA"}
                        </button>
                        {showDetails && result.report && (
                          <div className="w-full overflow-x-auto -mx-4 md:mx-0 scrollbar-thin">
                            <div className="inline-block min-w-full align-middle px-4 md:px-0">
                              <table className="w-full border-collapse border-2 md:border-3 border-black dark:border-gray-600 font-mono text-xs">
                                <thead>
                                  <tr className="bg-black dark:bg-gray-900 text-white">
                                    <th className="border border-black dark:border-gray-600 p-2 text-left font-bold text-xs">CHECK</th>
                                    <th className="border border-black dark:border-gray-600 p-2 text-left font-bold text-xs">STATUS</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {Object.entries(result.report).map(([key, value], index) => (
                                    <tr key={key} className={`${index % 2 === 0 ? 'bg-gray-50 dark:bg-gray-900' : 'bg-white dark:bg-gray-800'} hover:bg-yellow-100 dark:hover:bg-gray-700 transition-colors`}>
                                      <td className="border border-black dark:border-gray-600 p-2 text-xs">{key}</td>
                                      <td className="border border-black dark:border-gray-600 p-2">
                                        <span className={`inline-block px-2 py-1 font-bold text-xs ${value ? 'bg-green-500' : 'bg-red-300'}`}>
                                          {value ? '✅' : '❌'}
                                        </span>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
