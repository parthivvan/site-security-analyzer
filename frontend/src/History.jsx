import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from './api';

/** Compute a 0-100 security score from the raw report object returned by the API */
function computeScore(report) {
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
}

/** Count how many checks passed / failed */
function countIssues(report) {
  if (!report) return { passed: 0, failed: 0 };
  const checks = [
    report.https,
    report.hsts,
    report.content_security_policy,
    !!report.x_frame_options,
    !!report.x_content_type_options,
    !!report.referrer_policy,
    report.permissions_policy,
    report.dns_spf,
    report.dns_dmarc,
    !report.server_header,
  ];
  const passed = checks.filter(Boolean).length;
  return { passed, failed: checks.length - passed };
}

function scoreLabel(s) {
  if (s >= 80) return 'EXCELLENT';
  if (s >= 60) return 'GOOD';
  if (s >= 40) return 'MODERATE';
  return 'CRITICAL';
}

function scoreBg(s) {
  if (s >= 80) return 'bg-brutal-green dark:bg-emerald-600 text-black';
  if (s >= 60) return 'bg-brutal-blue dark:bg-[#5865F2] text-white';
  if (s >= 40) return 'bg-brutal-yellow dark:bg-amber-500 text-black';
  return 'bg-brutal-red dark:bg-[#ED4245] text-white';
}

export default function History() {
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Filtering and sorting state
  const [searchTerm, setSearchTerm] = useState('');
  const [scoreFilter, setScoreFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    // Use api.isAuthenticated() which checks TokenManager (sessionStorage ssa_access_token
    // + localStorage ssa_refresh_token). Do NOT use localStorage.getItem('auth_token') —
    // that key never exists; the correct key is 'ssa_access_token' in sessionStorage.
    if (!api.isAuthenticated()) {
      setError('Please log in to view history');
      setLoading(false);
      return;
    }

    (async () => {
      try {
        // Let the api client inject the token automatically via TokenManager
        const data = await api.get('/auth/history');
        setItems(data.scans || []);
        setFilteredItems(data.scans || []);
      } catch (e) {
        if (e.status === 401) {
          // Clear tokens via TokenManager (not via wrong localStorage key)
          api.tokenManager.clearTokens();
          navigate('/login');
          return;
        }
        console.error('History fetch error:', e);
        setError(e.message || 'Failed to load history');
      } finally {
        setLoading(false);
      }
    })();
  }, [navigate]);

  // Apply filters and sorting whenever dependencies change
  useEffect(() => {
    let filtered = [...items];

    // Search filter — matches url
    if (searchTerm) {
      filtered = filtered.filter(scan =>
        (scan.url || '').toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Score-based filter
    if (scoreFilter !== 'all') {
      filtered = filtered.filter(scan => {
        const s = computeScore(scan.report);
        if (scoreFilter === 'critical') return s < 40;
        if (scoreFilter === 'moderate') return s >= 40 && s < 60;
        if (scoreFilter === 'good') return s >= 60 && s < 80;
        if (scoreFilter === 'excellent') return s >= 80;
        return true;
      });
    }

    // Sorting
    filtered.sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'date') {
        cmp = new Date(a.created_at || 0) - new Date(b.created_at || 0);
      } else if (sortBy === 'score') {
        cmp = computeScore(a.report) - computeScore(b.report);
      } else if (sortBy === 'passed') {
        cmp = countIssues(a.report).passed - countIssues(b.report).passed;
      } else if (sortBy === 'failed') {
        cmp = countIssues(a.report).failed - countIssues(b.report).failed;
      }
      return sortOrder === 'asc' ? cmp : -cmp;
    });

    setFilteredItems(filtered);
    setCurrentPage(1);
  }, [items, searchTerm, scoreFilter, sortBy, sortOrder]);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const exportToCSV = () => {
    const headers = ['Date', 'URL', 'Score', 'Grade', 'Passed', 'Failed', 'HTTPS', 'HSTS', 'CSP'];
    const rows = filteredItems.map(scan => {
      const s = computeScore(scan.report);
      const { passed, failed } = countIssues(scan.report);
      const when = scan.created_at ? new Date(scan.created_at).toLocaleString() : 'N/A';
      return [
        when,
        scan.url || '',
        s,
        scoreLabel(s),
        passed,
        failed,
        scan.report?.https ? 'Yes' : 'No',
        scan.report?.hsts ? 'Yes' : 'No',
        scan.report?.content_security_policy ? 'Yes' : 'No',
      ];
    });

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `scan-history-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
  };

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredItems.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);

  return (
    <div className="min-h-screen bg-brutal-bg dark:bg-[#1A1D21] p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-black font-mono mb-2 dark:text-white">Scan History</h1>
          <p className="text-brutal-black/60 dark:text-[#8E9297]">View all your previous security scans</p>
        </div>

        <div className="card-brutal bg-white dark:bg-[#242629] p-4 md:p-6">
          {/* Header Actions */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
            <Link
              to="/analyze"
              className="btn-brutal bg-brutal-blue dark:bg-[#5865F2] text-white px-6 py-3 inline-block hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
            >
              ← New Scan
            </Link>
            <button
              onClick={exportToCSV}
              className="btn-brutal bg-brutal-green dark:bg-[#00D9A3] dark:text-black px-6 py-3 hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
              disabled={filteredItems.length === 0}
            >
              📥 Export CSV
            </button>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 dark:bg-[#1E2124] border-2 border-brutal-black dark:border-[#43474D]">
            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">SEARCH URL</label>
              <input
                type="text"
                className="input-brutal text-sm w-full"
                placeholder="Search by URL..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">SCORE FILTER</label>
              <select
                className="input-brutal text-sm w-full"
                value={scoreFilter}
                onChange={(e) => setScoreFilter(e.target.value)}
              >
                <option value="all">All Scans</option>
                <option value="excellent">Excellent (80+)</option>
                <option value="good">Good (60-79)</option>
                <option value="moderate">Moderate (40-59)</option>
                <option value="critical">Critical (&lt;40)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold mb-2 font-mono dark:text-white">PER PAGE</label>
              <select
                className="input-brutal text-sm w-full"
                value={itemsPerPage}
                onChange={(e) => setItemsPerPage(Number(e.target.value))}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
            </div>
          </div>

          {/* Results Count */}
          <div className="mb-4 text-sm font-mono dark:text-white">
            Showing {currentItems.length} of {filteredItems.length} scans
            {searchTerm && ` (filtered from ${items.length} total)`}
          </div>

          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-brutal-black dark:border-[#43474D] border-t-brutal-blue dark:border-t-[#5865F2]"></div>
              <p className="mt-4 text-brutal-black/60 dark:text-[#8E9297] font-mono">Loading scans...</p>
            </div>
          )}

          {!loading && error && (
            <div className="bg-brutal-red/10 dark:bg-[#ED4245]/20 border-3 border-brutal-red dark:border-[#ED4245] p-6">
              <p className="text-brutal-red dark:text-[#ED4245] font-bold">⚠️ {error}</p>
            </div>
          )}

          {!loading && !error && filteredItems.length === 0 && (
            <div className="text-center py-12 border-3 border-brutal-black/20 dark:border-[#43474D]">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-xl font-bold mb-2 dark:text-white">No scans found</p>
              <p className="text-brutal-black/60 dark:text-[#8E9297] mb-6">
                {searchTerm || scoreFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Run your first security scan to see it here!'}
              </p>
              <Link
                to="/analyze"
                className="btn-brutal bg-brutal-green dark:bg-[#00D9A3] dark:text-[#1A1D21] px-8 py-3 inline-block font-bold"
              >
                Start Scanning →
              </Link>
            </div>
          )}

          {!loading && !error && currentItems.length > 0 && (
            <>
              <div className="overflow-x-auto -mx-2 md:mx-0">
                <div className="inline-block min-w-full align-middle">
                  <table className="min-w-full border-collapse border-3 border-brutal-black dark:border-[#43474D] font-mono text-xs md:text-sm">
                    <thead>
                      <tr className="bg-brutal-black dark:bg-[#2C2F33] text-white">
                        <th
                          className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold cursor-pointer hover:bg-brutal-blue dark:hover:bg-[#5865F2] transition-colors"
                          onClick={() => handleSort('date')}
                        >
                          DATE {sortBy === 'date' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold">
                          URL
                        </th>
                        <th
                          className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold cursor-pointer hover:bg-brutal-blue dark:hover:bg-[#5865F2] transition-colors"
                          onClick={() => handleSort('score')}
                        >
                          SCORE {sortBy === 'score' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold">
                          GRADE
                        </th>
                        <th
                          className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold cursor-pointer hover:bg-brutal-blue dark:hover:bg-[#5865F2] transition-colors"
                          onClick={() => handleSort('passed')}
                        >
                          PASSED {sortBy === 'passed' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th
                          className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold cursor-pointer hover:bg-brutal-blue dark:hover:bg-[#5865F2] transition-colors"
                          onClick={() => handleSort('failed')}
                        >
                          FAILED {sortBy === 'failed' && (sortOrder === 'asc' ? '↑' : '↓')}
                        </th>
                        <th className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 text-left font-bold">
                          ACTIONS
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentItems.map((scan, idx) => {
                        const when = scan.created_at ? new Date(scan.created_at).toLocaleString() : 'N/A';
                        const s = computeScore(scan.report);
                        const { passed, failed } = countIssues(scan.report);

                        return (
                          <tr key={scan.id || idx} className={idx % 2 === 0 ? 'bg-white dark:bg-[#1E2124]' : 'bg-gray-50 dark:bg-[#242629]'}>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 dark:text-[#E4E6EA] whitespace-nowrap">{when}</td>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3 dark:text-[#E4E6EA] max-w-xs truncate" title={scan.url}>
                              {truncate(scan.url, 45)}
                            </td>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3">
                              <span className={`inline-block px-2 py-1 font-bold text-xs ${scoreBg(s)}`}>
                                {s}%
                              </span>
                            </td>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3">
                              <span className={`inline-block px-2 py-1 font-bold text-xs ${scoreBg(s)}`}>
                                {scoreLabel(s)}
                              </span>
                            </td>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3">
                              <span className="inline-block px-2 py-1 bg-brutal-green dark:bg-emerald-600 text-black font-bold text-xs">
                                ✅ {passed}
                              </span>
                            </td>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3">
                              <span className={`inline-block px-2 py-1 font-bold text-xs ${failed > 0 ? 'bg-brutal-red dark:bg-[#ED4245] text-white' : 'bg-gray-200 dark:bg-[#1E2124] dark:text-[#8E9297]'}`}>
                                {failed > 0 ? '❌' : '✅'} {failed}
                              </span>
                            </td>
                            <td className="border-2 border-brutal-black dark:border-[#43474D] p-2 md:p-3">
                              <Link
                                to={`/analyze?url=${encodeURIComponent(scan.url || '')}`}
                                className="inline-block px-3 py-1 bg-brutal-blue dark:bg-[#5865F2] text-white text-xs font-bold hover:opacity-80 transition-all"
                              >
                                Re-scan
                              </Link>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex flex-col md:flex-row justify-between items-center gap-4">
                  <div className="text-sm font-mono dark:text-white">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="btn-brutal px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ««
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="btn-brutal px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      « Prev
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="btn-brutal px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next »
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="btn-brutal px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      »»
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n - 1) + '…' : str;
}
