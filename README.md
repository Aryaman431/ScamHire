# HireShield

**Evidence-driven recruitment scam and risk analysis platform.**

Analyze job postings, recruitment emails, offer letters, PDFs, and screenshots for scam signals. Returns an explainable risk score backed by deterministic rules and AI extraction via Amazon Bedrock.

---

## Features

- **AI-Powered Analysis** -- Amazon Bedrock (Claude) extracts structured risk signals and entities from raw job text, PDFs, or screenshots.
- **Deterministic Risk Engine** -- Reproducible, explainable score calculated from weighted signal categories; no black-box outputs.
- **AWS-Native Architecture** -- S3 for file storage, DynamoDB for analysis records, Bedrock for AI, Lambda/API Gateway ready.
- **Document Upload** -- PDF parsing with page-count limits; magic-byte validation for images.
- **Demo Mode** -- Works without any authentication configuration for quick hackathon demos.
- **Local Development** -- Runs without Docker, PostgreSQL, or any external dependencies (uses in-memory storage when AWS credentials not configured).

---

## Tech Stack

### Frontend
| | |
|---|---|
| Framework | Next.js 16 (React 19, App Router) |
| Styling | Tailwind CSS v4 |
| Animation | Framer Motion |
| Icons | Lucide React |
| Auth | Clerk (optional, demo mode default) |

### Backend
| | |
|---|---|
| Framework | FastAPI |
| AI | Amazon Bedrock (Claude 3.5 Sonnet) |
| Storage | Amazon S3 |
| Database | Amazon DynamoDB |
| Auth | JWT verification / demo mode |
| Lambda Adapter | Mangum |

### AWS Services
| Service | Purpose |
|---|---|
| S3 | Stores uploaded job postings, PDFs, screenshots |
| DynamoDB | Stores analysis records and history |
| Bedrock | AI-powered extraction and analysis |
| Lambda | Backend deployment target (via Mangum) |
| API Gateway | Public API layer |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS account with Bedrock access enabled for Claude (optional for local dev)

### 1. Configure environment

`ash
cd backend
cp .env.example .env
# Edit .env with your AWS credentials (optional for local development)
`

### 2. Start the backend

`ash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
`

### 3. Start the frontend

`ash
cd frontend
npm install
npm run dev
`

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## AWS Setup Required

1. **Enable Amazon Bedrock model access:**
   - Go to AWS Console > Bedrock > Model access
   - Enable Anthropic Claude 3.5 Sonnet v2 (or your preferred model)

2. **Create S3 bucket:**
   `ash
   aws s3 mb s3://hireshield-uploads --region us-east-1
   `

3. **DynamoDB table is auto-created** on first backend startup.

4. **IAM permissions needed:**
   `json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:HeadObject"
         ],
         "Resource": "arn:aws:s3:::hireshield-uploads/*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "dynamodb:PutItem",
           "dynamodb:GetItem",
           "dynamodb:Scan",
           "dynamodb:CreateTable"
         ],
         "Resource": "arn:aws:dynamodb:*:*:table/hire-shield-analyses"
       }
     ]
   }
   `

---

## Architecture

`
Browser (Next.js)
    |
    +-- /analyze          -> Job input form -> POST /api/v1/jobs/analyze
    +-- /analyze/result/[id] -> Animated risk report
    +-- /dashboard        -> Intelligence command center
          |
          |  (JWT Bearer token in Authorization header)
          v
FastAPI Backend (Lambda-compatible via Mangum)
    +-- POST /api/v1/jobs/analyze
    |       +-- BedrockProvider -> Amazon Bedrock (signal extraction)
    |       +-- RiskEngine (deterministic scoring)
    |       +-- DynamoDB (persist results)
    +-- POST /api/v1/jobs/analyze-file
    |       +-- S3 (store uploaded file)
    |       +-- BedrockProvider -> Amazon Bedrock
    |       +-- RiskEngine
    |       +-- DynamoDB
    +-- GET  /api/v1/jobs/{id}/result
    |       +-- DynamoDB (retrieve result)
    +-- GET  /api/v1/jobs/{id}/historical-intelligence
    +-- GET  /api/v1/jobs/{id}/verification
    +-- POST /api/v1/jobs/{id}/verification/recheck

New API Endpoints (per requirements):
    +-- GET  /health
    +-- POST /api/analyze
    +-- POST /api/analyze/file
    +-- GET  /api/analyses
    +-- GET  /api/analyses/{analysis_id}
`

### Key Design Decisions
- **AI is extraction-only.** Bedrock quotes evidence verbatim; it never assigns scores.
- **Risk scoring is deterministic.** ackend/app/risk/engine.py applies fixed weights per signal category, producing reproducible scores.
- **AWS-native.** No relational database, no Docker dependency. Runs on Lambda behind API Gateway.
- **Graceful degradation.** Falls back to keyword heuristics when Bedrock is unavailable. Demo mode works without any authentication.
- **Local-first development.** Uses in-memory storage when AWS credentials are not configured.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| AWS_REGION | Yes | AWS region for all services |
| AWS_ACCESS_KEY_ID | Local dev only | AWS credentials (use IAM roles in production) |
| AWS_SECRET_ACCESS_KEY | Local dev only | AWS credentials (use IAM roles in production) |
| S3_BUCKET | Yes | S3 bucket name for file uploads |
| DYNAMODB_TABLE | Yes | DynamoDB table name for analysis records |
| BEDROCK_MODEL_ID | Yes | Bedrock model ID (default: Claude 3.5 Sonnet v2) |
| CORS_ORIGINS | No | Comma-separated allowed origins |
| NEXT_PUBLIC_API_URL | Frontend | Public-facing API URL |
| MAX_UPLOAD_SIZE_MB | No | Max file upload size (default: 10) |
| MAX_PDF_PAGES | No | Max pages per PDF (default: 20) |

---

## API Endpoints

### Health Check
`
GET /health
`
Response:
`json
{
  "status": "ok",
  "service": "hireshield-api"
}
`

### Analyze Text (New API)
`
POST /api/analyze
Content-Type: application/json

{
  "text": "...job posting or recruitment message..."
}
`
Response:
`json
{
  "analysis_id": "...",
  "risk_level": "HIGH",
  "risk_score": 82,
  "summary": "...",
  "indicators": [
    {
      "type": "UPFRONT_PAYMENT",
      "severity": "HIGH",
      "evidence": "...",
      "explanation": "..."
    }
  ],
  "recommendations": [
    "Do not make any payment",
    "Verify the employer through its official website"
  ]
}
`

### Analyze File (New API)
`
POST /api/analyze/file
Content-Type: multipart/form-data

file: <PDF/image/text file>
`
Response: Same as /api/analyze

### Analysis History (New API)
`
GET /api/analyses
`
Response:
`json
{
  "analyses": [
    {
      "analysis_id": "...",
      "created_at": "...",
      "input_type": "TEXT",
      "risk_score": 82,
      "risk_level": "HIGH",
      "summary": "..."
    }
  ]
}
`

`
GET /api/analyses/{analysis_id}
`
Response: Full analysis detail with indicators, recommendations, AI findings, and deterministic findings.

### Frontend-Compatible Endpoints (Legacy)
`
POST /api/v1/jobs/analyze
POST /api/v1/jobs/analyze-file
GET  /api/v1/jobs/{id}/result
GET  /api/v1/jobs/history/list
GET  /api/v1/jobs/{id}/historical-intelligence
GET  /api/v1/jobs/{id}/verification
POST /api/v1/jobs/{id}/verification/recheck
`

---

## Local Development

The backend works locally **without**:
- Docker
- PostgreSQL
- pgvector
- Render
- AWS credentials (uses in-memory storage fallback)

Local development only requires:
- Python
- pip/venv
- AWS credentials configured through AWS CLI or environment (optional)

If AWS credentials are not configured, the backend automatically uses in-memory storage for DynamoDB and skips S3 uploads (file analysis will use heuristic extraction only).

---

## AWS Deployment Overview

1. **Package the application:**
   `ash
   cd backend
   pip install -r requirements.txt -t package/
   cp -r app package/
   cd package && zip -r ../function.zip .
   `

2. **Create Lambda function:**
   - Runtime: Python 3.11+
   - Handler: pp.main.handler
   - Upload unction.zip
   - Configure environment variables
   - Attach IAM role with permissions above

3. **Create API Gateway:**
   - REST API or HTTP API
   - Integrate with Lambda function
   - Configure CORS
   - Deploy stage

4. **Configure frontend:**
   - Set NEXT_PUBLIC_API_URL to API Gateway URL
   - Deploy frontend to Vercel/Amplify

---

## Project Structure

`
backend/
  app/
    __init__.py
    main.py                 # FastAPI app + Mangum handler
    core/
      config.py             # Pydantic settings
      dynamodb.py           # DynamoDB service (with local fallback)
      s3.py                 # S3 service
      rate_limit.py         # SlowAPI rate limiting
    api/
      __init__.py
      health.py             # GET /health
      analysis.py           # POST /api/analyze, POST /api/analyze/file
      history.py            # GET /api/analyses, GET /api/analyses/{id}
      jobs.py               # Frontend-compatible endpoints
      schemas.py            # Pydantic request/response models
    services/
      analysis_service.py   # Orchestrates AI + risk + persistence
    ai/
      __init__.py
      provider.py           # Abstract AI provider interface
      bedrock.py            # Bedrock implementation + heuristic fallback
      schemas.py            # AI extraction schemas
    risk/
      __init__.py
      rules.py              # Signal types and scores
      engine.py             # Deterministic risk calculation
      aggregation.py        # Risk level helpers
    auth/
      dependencies.py       # JWT auth + demo mode
  tests/
    test_health.py
    test_risk_engine.py
    test_dynamodb_service.py
    test_analysis_flow.py
  requirements.txt
  .env.example
  pytest.ini
`

---

## Testing

`ash
cd backend
python -m pytest tests/ -v
`

---

## Security

- Never hard-code AWS credentials
- Never commit secrets (.env is gitignored)
- Validate file types via magic bytes
- Validate upload size limits
- Sanitize filenames
- Configure CORS through environment variables
- Do not expose internal AWS errors directly
- Do not trust AI output blindly (validated against schema)
- Keep deterministic risk rules separate from AI reasoning

---

## License

MIT
