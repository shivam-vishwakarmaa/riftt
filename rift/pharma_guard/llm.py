import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from rag_retrieval import GuidelineRetriever

load_dotenv()

retriever = GuidelineRetriever()


def _get_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY")

def is_llm_configured() -> bool:
    """True when an LLM API key is available in env vars."""
    return bool(_get_api_key())


def _extract_json(text: str) -> Dict[str, Any]:
    payload = text.strip()
    if payload.startswith("```json"):
        payload = payload[7:]
    if payload.startswith("```"):
        payload = payload[3:]
    if payload.endswith("```"):
        payload = payload[:-3]
    payload = payload.strip()
    return json.loads(payload)


def _call_openai_json(prompt: str) -> Dict[str, Any]:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    host = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    url = f"{host}/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": "Return only valid JSON with no markdown.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=45,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text[:240]}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return _extract_json(content)


def _variant_context(variants: List[Dict[str, Any]], max_items: int = 25) -> List[Dict[str, Any]]:
    ctx = []
    for v in variants[:max_items]:
        ctx.append(
            {
                "rsid": v.get("rsid"),
                "gene": v.get("gene"),
                "allele": v.get("allele"),
                "genotype": v.get("genotype"),
                "function": v.get("function"),
                "quality_score": v.get("quality_score"),
                "read_depth": v.get("read_depth"),
            }
        )
    return ctx


def _guideline_options(drug: str) -> List[Dict[str, Any]]:
    options: List[Dict[str, Any]] = []
    try:
        phenos = retriever.get_all_phenotypes_for_drug(drug)
        for p in phenos:
            code = p.get("phenotype_code")
            if not code:
                continue
            g = retriever.get_guideline(drug, code)
            if g:
                options.append(
                    {
                        "phenotype_code": g.get("phenotype_code"),
                        "phenotype_name": g.get("phenotype_name"),
                        "summary": g.get("summary"),
                        "mechanism": g.get("mechanism"),
                        "recommendation": g.get("recommendation"),
                        "source": g.get("source"),
                        "guideline_url": g.get("guideline_url"),
                        "gene": g.get("gene"),
                    }
                )
    except Exception:
        return []
    return options


def add_structured_citations(explanation: Dict[str, Any], guideline: Optional[Dict[str, Any]], variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    explanation["variant_citations"] = []
    explanation["guideline_citations"] = []

    for v in variants[:10]:
        explanation["variant_citations"].append(
            {
                "rsid": v.get("rsid", "Unknown"),
                "gene": v.get("gene", "Unknown"),
                "allele": v.get("allele", "Unknown"),
                "function": v.get("function", "Unknown"),
                "genotype": v.get("genotype", "Unknown"),
                "dbSNP_url": f"https://www.ncbi.nlm.nih.gov/snp/{v.get('rsid', '')}",
            }
        )

    if guideline:
        explanation["guideline_citations"].append(
            {
                "type": "cpic_guideline",
                "source": guideline.get("source", "CPIC Guideline"),
                "url": guideline.get("guideline_url", ""),
                "phenotype": guideline.get("phenotype_name", ""),
                "gene": guideline.get("gene", ""),
                "summary": guideline.get("summary", ""),
                "recommendation": guideline.get("recommendation", ""),
            }
        )
    else:
        explanation["guideline_citations"].append(
            {
                "type": "cpic_reference",
                "source": "CPIC Guidelines",
                "url": "https://cpicpgx.org/guidelines/",
                "description": "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            }
        )

    return explanation


def get_fallback(phenotype: str, error_msg: str, variants: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    explanation = {
        "summary": f"Patient exhibits {phenotype} phenotype requiring clinical review.",
        "mechanism": f"LLM generation unavailable ({error_msg}). Refer to CPIC guidelines.",
        "recommendation": "Use CPIC-aligned dosing for the inferred phenotype and confirm with clinician review.",
    }
    return add_structured_citations(explanation, None, variants or [])


def get_llm_clinical_risk(drug: str, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    LLM-driven clinical decision:
    - risk label
    - severity
    - phenotype/diplotype/gene
    - CPIC-aligned recommendation
    """
    options = _guideline_options(drug)
    prompt = f"""
You are a pharmacogenomics clinical decision model.
Task: infer risk for DRUG={drug.upper()} from the provided VCF variants and CPIC options.

Allowed risk labels: Safe, Adjust Dosage, Toxic, Ineffective, Unknown.
Allowed cpic_level: A, B, C, D, N/A.

Variants (JSON):
{json.dumps(_variant_context(variants), ensure_ascii=True)}

CPIC options for this drug (JSON):
{json.dumps(options, ensure_ascii=True)}

Return ONLY valid JSON with exactly these keys:
{{
  "label": "...",
  "severity": "none|low|moderate|high|critical|unknown",
  "phenotype": "...",
  "diplotype": "...",
  "gene": "...",
  "recommendation": "...",
  "cpic_level": "...",
  "llm_confidence_percent": 0-100
}}

Constraints:
- Prefer CPIC-grounded reasoning.
- If evidence is insufficient, use label="Unknown" and conservative recommendation.
"""
    data = _call_openai_json(prompt)
    label_raw = str(data.get("label", "Unknown")).strip()
    label_map = {
        "safe": "Safe",
        "adjust dosage": "Adjust Dosage",
        "adjust": "Adjust Dosage",
        "toxic": "Toxic",
        "ineffective": "Ineffective",
        "unknown": "Unknown",
    }
    label = label_map.get(label_raw.lower(), "Unknown")

    normalized = {
        "label": label,
        "severity": str(data.get("severity", "unknown")),
        "phenotype": str(data.get("phenotype", "Unknown")),
        "diplotype": str(data.get("diplotype", "*1/*1")),
        "gene": str(data.get("gene", "Unknown")),
        "recommendation": str(data.get("recommendation", "Insufficient data for recommendation.")),
        "cpic_level": str(data.get("cpic_level", "N/A")).upper(),
        "llm_confidence_percent": float(data.get("llm_confidence_percent", 70)),
    }
    return normalized


def get_explanation(drug: str, phenotype: str, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    LLM-generated biological explanation, grounded in CPIC guideline when available.
    """
    guideline = retriever.get_guideline(drug, phenotype)
    if guideline:
        prompt = f"""
Based STRICTLY on this CPIC guideline:
DRUG={guideline['drug_name']}
GENE={guideline['gene']}
PHENOTYPE={guideline['phenotype_name']} ({guideline['phenotype_code']})
SUMMARY={guideline['summary']}
MECHANISM={guideline['mechanism']}
RECOMMENDATION={guideline['recommendation']}
SOURCE={guideline['source']}

Return ONLY valid JSON with keys:
{{
  "summary": "one sentence",
  "mechanism": "brief biological explanation",
  "recommendation": "brief clinical recommendation aligned with the guideline"
}}
"""
    else:
        prompt = f"""
Act as a clinical pharmacologist.
Explain why a patient with phenotype={phenotype} has altered risk for drug={drug}.
Return ONLY valid JSON:
{{"summary":"one sentence","mechanism":"brief biological explanation","recommendation":"brief clinical recommendation"}}
"""

    try:
        explanation = _call_openai_json(prompt)
        if not isinstance(explanation, dict):
            explanation = {
                "summary": f"Patient exhibits {phenotype} phenotype for {drug}.",
                "mechanism": "LLM output could not be parsed; please review CPIC guidance.",
                "recommendation": "Follow CPIC-aligned dosing with clinician review.",
            }
        if not explanation.get("recommendation"):
            explanation["recommendation"] = (
                guideline.get("recommendation")
                if guideline and guideline.get("recommendation")
                else "Use CPIC-aligned dosing for this phenotype with clinician oversight."
            )
        return add_structured_citations(explanation, guideline, variants)
    except Exception as e:
        return get_fallback(phenotype, str(e), variants)
