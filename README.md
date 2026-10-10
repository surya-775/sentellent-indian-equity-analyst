# Personal Agentic AI Indian-Equity Analyst (RAG)
### Sentellent Hiring Challenge — Full Stack AI SDE Intern

[![CI/CD AWS Deployment](https://github.com/surya-775/sentellent-indian-equity-analyst/actions/workflows/deploy.yml/badge.svg)](https://github.com/surya-775/sentellent-indian-equity-analyst/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![AWS ECS Fargate](https://img.shields.io/badge/AWS-ECS%20Fargate-orange.svg)](https://aws.amazon.com/fargate/)
[![PostgreSQL pgvector](https://img.shields.io/badge/Vector%20Store-pgvector-blue.svg)](https://github.com/pgvector/pgvector)

An autonomous, production-grade **Equity Research Chief of Staff for the NSE / BSE** that runs in the cloud, ingests real-time Indian fundamentals & news into a vector database, dynamically learns the investor's persona, and generates strictly grounded, cited recommendations in **INR (₹)** with zero hallucinations.

---

## 🌐 Live AWS Production Endpoints
- **Live Web Application (Next.js Dashboard)**: [http://indian-equity-analyst-alb-1057081145.ap-south-1.elb.amazonaws.com](http://indian-equity-analyst-alb-1057081145.ap-south-1.elb.amazonaws.com)
- **FastAPI Backend Health API**: [http://indian-equity-analyst-alb-1057081145.ap-south-1.elb.amazonaws.com/api/health](http://indian-equity-analyst-alb-1057081145.ap-south-1.elb.amazonaws.com/api/health)
- **Interactive OpenAPI Documentation**: [http://indian-equity-analyst-alb-1057081145.ap-south-1.elb.amazonaws.com/docs](http://indian-equity-analyst-alb-1057081145.ap-south-1.elb.amazonaws.com/docs)
- **GitHub Repository**: [https://github.com/surya-775/sentellent-indian-equity-analyst](https://github.com/surya-775/sentellent-indian-equity-analyst)

---

## 🏛️ System Architecture

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Next.js 14 Frontend UI                           │
 │     Watchlist Hub  •  Agentic Chat  •  Dynamic Persona Memory Card    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │  HTTP / REST (Port 3000 / 80)
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │               AWS Application Load Balancer (ALB)                     │
 │          /api/* ──► FastAPI Backend  |  /* ──► Next.js                │
 └─────────────────┬───────────────────────────────────┬──────────────────┘
                   │                                   │
 ┌─────────────────▼─────────────────────┐  ┌──────────▼──────────────────┐
 │   FastAPI Backend (ECS Fargate)       │  │ Next.js Web (ECS Fargate)   │
 │   - LangGraph Agentic Brain           │  │ Multi-stage Alpine container│
 │   - Idempotent Ingestion Engine       │  └─────────────────────────────┘
 │   - Strict Anti-Hallucination Guard   │
 └─────────────┬─────────────────┬───────┘
               │                 │
 ┌─────────────▼──────┐   ┌──────▼────────────────────────────────────────┐
 │ Indian Data Stream │   │   Amazon RDS PostgreSQL (pgvector)            │
 │ • Screener.in      │   │   - stocks (Fundamentals in ₹)                │
 │ • NSE / yfinance   │   │   - news_articles (SHA-256 dedup, embeddings) │
 │ • ET, MC, Mint RSS │   │   - user_personas (Rules + Persona vector)    │
 └────────────────────┘   └───────────────────────────────────────────────┘
```

---

## 🚀 Key Features & Architectural Highlights

### 1. LangGraph Brain & Dynamic Persona Memory
- **Learns from Chat**: Conversational statements such as *"I'm a conservative, dividend-focused investor and I avoid high-debt companies"* dynamically update the user's memory graph and persona vector in `pgvector`.
- **Hard Rule Screening**: Instantly screens out companies whose Debt-to-Equity exceeds the learned threshold or whose dividend yield is below requirements.
- **Multi-Factor Scoring**: Evaluates candidate equities across **Growth, Value, Stability, Momentum, and Quality** weighted against the investor persona.

### 2. Autonomous Indian Market Ingestion Engine
- **Sources**: Scrapes fundamentals from Screener.in with yfinance (`.NS` / `.BO`) fallback; streams financial news RSS feeds from **Economic Times, Moneycontrol, LiveMint, and Business Standard**.
- **All Figures in INR**: Market cap in ₹ Crores, current prices in ₹, P/E, ROCE, ROE, and Debt-to-Equity.
- **Idempotency & Concurrent Safety**: SHA-256 fingerprint deduplication prevents duplicate indexing. Thread mutex locks per ticker guarantee race-condition-free concurrent ingestion.
- **Rolling Sentiment**: Automated NLP enrichment extracts financial sentiment and key events (e.g., *"Rising debt"*, *"Capex expansion"*, *"Dividend declaration"*) to maintain a rolling stock sentiment score.

### 3. Strict Citations & Anti-Hallucination Guardrail
- **Grounded Citations**: Every claim, metric, and recommendation links directly to an exact source doc (Screener.in fundamentals row or verified news article).
- **Anti-Hallucination Guarantee**: If asked about an unindexed ticker or unavailable metric, the agent explicitly replies:
  > *"I don't have that in the ingested data. Please follow or ingest this ticker first to index its fundamentals and news into the vector store."*

### 4. Authentication (Google Cloud Console OAuth)
- **Evaluator Access**: Pre-configured with Sentellent test users:
  - `harisankar@sentellent.com`
  - `naga@sentellent.com`
- Includes demo evaluation mode for instant review without credential friction.

---

## 🛠️ Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| **Frontend** | Next.js 14, React 18, Tailwind CSS, Lucide | Responsive, dark-mode financial dashboard |
| **Backend** | Python 3.10, FastAPI, Uvicorn | Asynchronous, typed REST API |
| **Agent / Memory** | LangGraph, LangChain | State graph routing, dynamic long-term memory |
| **Vector Store** | PostgreSQL + pgvector | Hybrid relational & 1536-dim vector similarity |
| **Market Data** | Screener.in, yfinance, Indian RSS Feeds | Free, reliable Indian exchange coverage (NSE/BSE) |
| **Infrastructure** | Terraform (IaC) | Declarative AWS provisioning |
| **Cloud Target** | AWS (ECS Fargate, ALB, RDS PostgreSQL) | Production container orchestration |
| **CI/CD** | GitHub Actions | Automated test suite, ECR build, and ECS rollout |

---

## 📦 Local Development (Quickstart)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (Optional for container testing)

### Option A: Local Native Setup

#### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/your-username/indian-equity-analyst.git
cd indian-equity-analyst

# Create and activate virtual environment
python -m venv backend/venv
source backend/venv/bin/activate   # On Windows: backend\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run test suite
pytest backend/tests -v

# Start FastAPI backend
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Backend will be live at `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend will be live at `http://localhost:3000`.

---

### Option B: One-Command Docker Compose
```bash
docker-compose up --build
```
This starts:
- **PostgreSQL 15 with pgvector** on port `5432`
- **FastAPI Agent Backend** on port `8000`
- **Next.js Web UI** on port `3000`

---

## ☁️ AWS Cloud Infrastructure (Terraform)

All infrastructure is codified in the [`terraform/`](./terraform) directory:

```
terraform/
├── versions.tf          # AWS provider (~> 5.0)
├── variables.tf         # Regions, subnets, instance sizes
├── vpc.tf               # Multi-AZ VPC, Public & Private Subnets, IGW
├── security_groups.tf   # ALB, ECS Fargate, and RDS ingress/egress rules
├── rds.tf               # RDS PostgreSQL 15 with pgvector parameter group
├── ecr.tf               # Elastic Container Registry for backend & frontend
├── alb.tf               # Application Load Balancer with /api/* path routing
├── ecs.tf               # ECS Fargate Cluster, Task Definitions, and Services
└── outputs.tf           # ALB DNS URL, RDS Endpoint, ECR URLs
```

### Provisioning to AWS:
```bash
cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```

### Outputs Generated:
- `application_url`: Public URL of the Application Load Balancer
- `api_endpoint`: Backend API root (`http://<alb-dns>/api`)
- `rds_postgres_endpoint`: Amazon RDS PostgreSQL instance with `pgvector`
- `backend_ecr_repository_url`: ECR image repo for FastAPI
- `frontend_ecr_repository_url`: ECR image repo for Next.js

---

## 🔄 CI/CD Automation (GitHub Actions)

The repository includes a production workflow in [`.github/workflows/deploy.yml`](./.github/workflows/deploy.yml):

1. **Continuous Integration**:
   - Executes backend unit & integration tests (`pytest backend/tests -v`).
   - Verifies Terraform syntax and configuration (`terraform validate`).
2. **Continuous Deployment** (on push to `main`):
   - Authenticates with AWS via OIDC / GitHub Secrets.
   - Builds multi-stage Docker images for Frontend and Backend.
   - Pushes images to Amazon ECR.
   - Applies Terraform infrastructure updates.
   - Issues `aws ecs update-service --force-new-deployment` for rolling, zero-downtime deployment.

---

## 🧪 Verification & Test Coverage

Run the backend test suite:
```bash
pytest backend/tests -v
```

Verified test suite (9 / 9 Passing):
- `test_persona_rule_extraction`: Asserts conversational extraction of risk profile and debt rules.
- `test_persona_screening_out_high_debt`: Verifies that high-debt stocks are algorithmically excluded.
- `test_anti_hallucination_on_unknown_stock`: Validates that queries for unindexed stocks return the strict *"I don't have that in the ingested data"* guardrail.
- `test_ingestion_idempotency_and_deduplication`: Validates that repeated ingestions do not duplicate articles or corrupt state.
- `test_sentiment_and_event_extraction`: Confirms NLP tagging of financial events and sentiment impact.
- `test_whitelisted_test_user_allowed`: Confirms Sentellent test users (`harisankar@sentellent.com`, `naga@sentellent.com`) are authenticated seamlessly.
- `test_arbitrary_unverified_email_strictly_rejected`: Validates strict rejection (HTTP 401) of unverified random emails without Google OAuth token.
- `test_invalid_google_token_rejected`: Rejects forged or expired Google OAuth tokens.
- `test_verified_google_token_accepted`: Verifies cryptographic token authentication with Google OAuth API.

---

## 📋 Evaluation Checklist

- [x] **Frontend**: Next.js 14 clean dashboard with watchlist, real-time chat, and persona view.
- [x] **Backend**: FastAPI with typed routes, Pydantic, and background services.
- [x] **AI / Agent Framework**: LangGraph state graph with dynamic persona memory and intent routing.
- [x] **Vector Store**: pgvector support on PostgreSQL with cosine similarity fallback.
- [x] **Indian Market Data**: Screener.in + NSE quotes in INR (`₹` / `Rs.`).
- [x] **Financial News**: RSS feeds from ET, Moneycontrol, LiveMint, Business Standard with SHA-256 dedup.
- [x] **Anti-Hallucination**: Enforced grounding and cited answers.
- [x] **Cloud & IaC**: Complete Terraform scripts for AWS ECS Fargate + RDS pgvector + ALB.
- [x] **CI/CD**: GitHub Actions deployment pipeline for continuous delivery.
- [x] **OAuth Ready**: Configured for `harisankar@sentellent.com` and `naga@sentellent.com`.
