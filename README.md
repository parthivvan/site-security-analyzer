"# 🔒 Site Security Analyzer

> **Professional website security scanner with comprehensive vulnerability detection, real-time scanning, and detailed reporting.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18.0+-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/fastapi-0.100+-green.svg)](https://fastapi.tiangolo.com)

## 🌟 Features

### Core Functionality
- ⚡ **Lightning-Fast Scanning** - Analyze websites in seconds
- 🔍 **Comprehensive Security Checks** - SSL/TLS, headers, DNS records, vulnerabilities
- 📊 **Detailed Reports** - Clear insights with severity ratings and remediation steps
- 🎯 **Real-Time Progress** - WebSocket-powered live scan updates
- 📈 **Security Score** - Easy-to-understand security rating system

### Advanced Features
- 🤖 **AI-Powered Recommendations** - Gemini AI integration for intelligent security advice
- 🕸️ **Attack Graph Visualization** - See vulnerability chains and attack paths
- 📜 **Scan History** - Track security over time with full history
- 🎓 **Educational Content** - Learn security concepts with interactive flashcards
- 🌙 **Dark Mode** - Comfortable viewing in any environment
- 📱 **Fully Responsive** - Works perfectly on mobile, tablet, and desktop

### Security Checks
- HTTPS/TLS verification
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- DNS security records (SPF, DMARC)
- Server information disclosure
- Cookie security attributes
- Permissions policy analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- npm or yarn

### Installation

#### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

### Running the Application

#### Start Backend (Flask - Simple)
```bash
cd backend
python app.py
# Server runs on http://localhost:5000
```

#### Start Backend (FastAPI - Advanced)
```bash
cd backend
uvicorn app_advanced:app --host 0.0.0.0 --port 8000
# Server runs on http://localhost:8000
# WebSocket endpoint: ws://localhost:8000/api/v2/ws/{scan_id}
```

#### Start Frontend
```bash
cd frontend
npm start
# Application runs on http://localhost:5173
```

## 📖 Usage

### Basic Scan
1. Navigate to `http://localhost:5173`
2. Click "Start Scanning" or go to `/analyze`
3. Enter a URL (e.g., `google.com` or `https://example.com`)
4. Click "ANALYZE"
5. View real-time scanning progress and results

### Features
- **Learn Page** (`/learn`): Interactive security education with flashcards
- **History Page** (`/history`): View all previous scans with filtering and sorting
- **Authentication**: Sign up/login to save scan history

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- React 18 with Vite
- React Router for navigation
- Tailwind CSS for styling
- WebSocket client for real-time updates

**Backend:**
- Flask (simple API)
- FastAPI (advanced API with WebSocket support)
- SQLAlchemy for database ORM
- dnspython for DNS queries
- PyJWT for authentication

**Database:**
- SQLite (development)
- PostgreSQL (production-ready)

### Project Structure
```
site-security-analyzer/
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── SiteSecurityAnalyzer.jsx
│   │   ├── History.jsx
│   │   ├── Learn.jsx
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── Landing.jsx
│   │   └── main.jsx
│   ├── public/
│   └── package.json
├── backend/
│   ├── app.py                 # Flask simple API
│   ├── app_advanced.py        # FastAPI advanced API
│   ├── core/                  # Core scanning logic
│   │   ├── crawler.py
│   │   ├── intelligence_engine.py
│   │   ├── attack_graph.py
│   │   └── risk_scorer.py
│   └── requirements.txt
├── extension/                 # Browser extension
└── README.md
```

## 🔒 Security Features

### OWASP Top 10 Checks
- Injection vulnerabilities
- Broken authentication
- Sensitive data exposure
- Security misconfiguration
- And more...

### Headers Analyzed
- Content-Security-Policy
- Strict-Transport-Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- Cross-Origin-Opener-Policy
- Cross-Origin-Embedder-Policy

## 📊 API Documentation

### Flask API (Port 5000)

#### POST /scan
Analyze a website for security issues.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "report": {
    "https": true,
    "hsts": true,
    "content_security_policy": false,
    ...
  },
  "explanation": "Security analysis summary..."
}
```

### FastAPI Advanced API (Port 8000)

#### POST /api/v2/scan
Start an advanced security scan with real-time updates.

**Request:**
```json
{
  "url": "https://example.com",
  "scan_type": "comprehensive",
  "include_exploits": true,
  "max_depth": 3
}
```

**Response:**
```json
{
  "scan_id": "uuid-here",
  "status": "queued",
  "message": "Scan initiated successfully"
}
```

#### WebSocket /api/v2/ws/{scan_id}
Real-time scan progress updates.

**Message Format:**
```json
{
  "type": "progress",
  "phase": "crawling",
  "progress": 45,
  "vulnerabilities_found": 3
}
```

#### GET /api/v2/history
Get scan history with pagination and filtering.

## 🛠️ Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Python linting
flake8 backend/

# JavaScript linting
cd frontend
npm run lint
```

## 🚀 Deployment

### Production Deployment

**Frontend (Vercel):**
```bash
cd frontend
vercel --prod
```

**Backend (Railway):**
```bash
railway up
```

### Environment Variables
Create `.env` file in backend directory:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/db
GEMINI_API_KEY=your-gemini-api-key
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- OWASP for security best practices
- FastAPI and React communities
- All contributors and testers

---

**Made with ❤️ for better web security**
" 
