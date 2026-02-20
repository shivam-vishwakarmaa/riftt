# 🧬 PharmaGuard – AI-Powered Pharmacogenomic Risk Engine

<div align="center">

[![Live Demo](https://img.shields.io/badge/Live-Demo-0ea5e9?style=for-the-badge)](https://riftt.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/shivam-vishwakarmaa/riftt)
[![RIFT 2026](https://img.shields.io/badge/RIFT-2026-ff6b6b?style=for-the-badge)](https://rift2026.dev)

🏆 RIFT 2026 Hackathon – Pharmacogenomics / Explainable AI Track  

[🎥 Demo Video](https://drive.google.com/file/d/1BZsVQW-aUkmaytKHzS1qh5ew9EAMHYm2/view?usp=drivesdk)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Core Features](#-core-features)
- [AI & Explainability](#-ai--explainability)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [Deployment](#-deployment)
- [Disclaimer](#-disclaimer)

---

## 🎯 Overview

PharmaGuard is a full-stack AI clinical decision support system that predicts pharmacogenomic drug response risks by analyzing patient genomic data (VCF files).

The system aligns with **CPIC (Clinical Pharmacogenetics Implementation Consortium)** guidelines and generates structured, explainable dosing recommendations.

---

## 🚨 The Problem

Adverse drug reactions cause over **100,000 deaths annually in the U.S.**

Many of these outcomes are preventable through pharmacogenomic testing — analyzing how genetic variants affect drug metabolism.

However, interpretation remains:
- Complex  
- Time-consuming  
- Difficult to standardize  

---

## 💡 Our Solution

PharmaGuard:

- Parses authentic VCF genomic files (v4.2, up to 5MB)
- Identifies variants across 6 high-impact pharmacogenes
- Predicts drug-specific risk classifications
- Generates LLM-powered explainable clinical reasoning
- Aligns outputs with CPIC evidence levels
- Provides structured JSON export

---

## 🧬 Core Features

### Supported Pharmacogenes
- CYP2D6  
- CYP2C19  
- CYP2C9  
- SLCO1B1  
- TPMT  
- DPYD  

### Supported Drugs
- Codeine  
- Warfarin  
- Clopidogrel  
- Simvastatin  
- Azathioprine  
- Fluorouracil  
- Fluoxetine  
- Paroxetine  
- Ibuprofen  
- Omeprazole  

### Risk Labels
- ✅ Safe  
- ⚠ Adjust Dosage  
- ❌ Toxic  
- ❌ Ineffective  
- ❓ Unknown  

### Clinical Capabilities
- CPIC Level A/B rule mapping
- Structured phenotype inference
- Polypharmacy interaction detection
- Confidence scoring
- JSON download export
- Multi-drug batch analysis

---

## 🤖 AI & Explainability

- GPT-powered clinical explanation engine
- Structured reasoning output (summary + mechanism + recommendation)
- Citations referencing variant data (dbSNP)
- Fallback deterministic rule engine when API unavailable
- CPIC-aligned dosing recommendations

---

## 💻 Tech Stack

### Backend
- FastAPI  
- Uvicorn  
- Python 3.10+  
- SQLite (CPIC rule database)  
- OpenAI API  

### Frontend
- Next.js 15  
- TypeScript  
- TailwindCSS  
- Deployed on Vercel  

### Infrastructure
- Backend hosted on Render  
- Frontend hosted on Vercel  

---

## 🏗 Architecture

VCF File  
↓  
FastAPI Variant Parser  
↓  
Gene Mapping Engine  
↓  
CPIC Rule Database (SQLite)  
↓  
Risk Classification Layer  
↓  
LLM Explanation Generator  
↓  
Next.js Clinical Dashboard  

---

## 📦 Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/shivam-vishwakarmaa/riftt.git
cd riftt
```

---

### 2️⃣ Backend Setup

```bash
cd rift/pharma_guard

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on:

```
http://localhost:8000
```

---

### 3️⃣ Frontend Setup

```bash
cd ../pharma-ui
npm install
npm run dev
```

Frontend runs on:

```
http://localhost:3000
```

---

## 🔐 Environment Variables

Create `.env` in backend directory:

```
OPENAI_API_KEY=your_openai_key
USE_PRECOMPUTED=false
```

Frontend environment variable:

```
NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com
```

---

## 🚀 Deployment

### Live Frontend
https://riftt.vercel.app/

### Live Backend
https://riftt-6pd5.onrender.com

---

## ⚠ Disclaimer

PharmaGuard is intended for research and educational purposes only.

It is not a substitute for licensed clinical decision-making or professional medical advice.

---

## 👨‍💻 Author

Built by Shivam Vishwakarma and whole team  
RIFT 2026 Hackathon Submission  

---

