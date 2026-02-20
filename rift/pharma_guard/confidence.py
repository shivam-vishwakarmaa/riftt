"""
Hybrid deterministic confidence scoring for PharmaGuard.

C = (W1 * Q_vcf) + (W2 * G_cpic) + (W3 * P_llm)
"""

import os
from typing import Any, Dict, List, Optional, Tuple

def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


# Pipeline-tunable parameters (override in environment if needed)
QUAL_MIN = _env_float("CONF_QUAL_MIN", 20.0)
QUAL_MAX = _env_float("CONF_QUAL_MAX", 200.0)
DP_MIN = _env_float("CONF_DP_MIN", 10.0)
DP_MAX = _env_float("CONF_DP_MAX", 100.0)

# Hybrid weights (sum auto-normalized)
W1 = _env_float("CONF_W_VCF", 0.40)  # VCF quality
W2 = _env_float("CONF_W_CPIC", 0.45)  # CPIC evidence strength
W3 = _env_float("CONF_W_LLM", 0.15)  # LLM consistency

_WEIGHT_SUM = W1 + W2 + W3
if _WEIGHT_SUM > 0:
    W1 = W1 / _WEIGHT_SUM
    W2 = W2 / _WEIGHT_SUM
    W3 = W3 / _WEIGHT_SUM
else:
    W1, W2, W3 = 0.40, 0.45, 0.15

CPIC_LEVEL_SCORE = {
    "A": 1.00,
    "B": 0.75,
    "C": 0.50,
    "D": 0.25,
    "N/A": 0.50,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _normalize_qual(qual: Optional[float]) -> float:
    if qual is None:
        return 0.60
    if qual <= QUAL_MIN:
        return 0.0
    if qual >= QUAL_MAX:
        return 1.0
    denom = max(1.0, QUAL_MAX - QUAL_MIN)
    return _clamp((qual - QUAL_MIN) / denom)


def _normalize_depth(depth: Optional[int]) -> float:
    if depth is None:
        return 0.60
    if depth <= DP_MIN:
        return 0.0
    if depth >= DP_MAX:
        return 1.0
    denom = max(1.0, DP_MAX - DP_MIN)
    return _clamp((float(depth) - DP_MIN) / denom)


def confidence_model_config() -> Dict[str, float]:
    """Expose active confidence model parameters for response/debugging."""
    return {
        "w_vcf": round(W1, 3),
        "w_cpic": round(W2, 3),
        "w_llm": round(W3, 3),
        "qual_min": round(QUAL_MIN, 3),
        "qual_max": round(QUAL_MAX, 3),
        "dp_min": round(DP_MIN, 3),
        "dp_max": round(DP_MAX, 3),
    }


def compute_vcf_quality_score(variants: List[Dict[str, Any]]) -> float:
    """
    Q_vcf component:
    - QUAL normalization
    - DP normalization
    - presence of GENE / STAR / RS annotations
    """
    if not variants:
        return 0.35

    qual_scores: List[float] = []
    depth_scores: List[float] = []
    annotation_scores: List[float] = []

    for variant in variants:
        qual_scores.append(_normalize_qual(variant.get("quality_score")))
        depth_scores.append(_normalize_depth(variant.get("read_depth")))

        has_gene = bool(variant.get("has_gene_annotation"))
        has_star = bool(variant.get("has_star_annotation"))
        has_rsid = bool(variant.get("has_rsid_annotation"))
        inferred_star = bool(str(variant.get("allele", "")).startswith("*"))

        # STAR from INFO is strongest; inferred STAR from mapping gets partial credit.
        star_credit = 1.0 if has_star else (0.5 if inferred_star else 0.0)
        annotation_scores.append((float(has_gene) + star_credit + float(has_rsid)) / 3.0)

    q_qual = sum(qual_scores) / len(qual_scores)
    q_depth = sum(depth_scores) / len(depth_scores)
    q_ann = sum(annotation_scores) / len(annotation_scores)

    return _clamp((0.45 * q_qual) + (0.35 * q_depth) + (0.20 * q_ann))


def compute_cpic_guideline_score(cpic_level: Optional[str]) -> float:
    level = (cpic_level or "N/A").strip().upper()
    return CPIC_LEVEL_SCORE.get(level, 0.50)


def compute_llm_consistency_score(risk_label: Optional[str], explanation: Optional[Dict[str, Any]]) -> float:
    """
    P_llm component:
    - lexical consistency between rule-based risk label and generated explanation
    - optional llm_confidence_percent if model provides it
    """
    if not explanation:
        return 0.75

    label = (risk_label or "").lower()
    text = f"{explanation.get('summary', '')} {explanation.get('mechanism', '')}".lower()

    high_cues = ["avoid", "toxic", "toxicity", "ineffective", "life-threatening", "severe"]
    moderate_cues = ["adjust", "reduce", "increase", "monitor", "consider", "dose"]
    low_cues = ["safe", "standard dose", "standard dosing", "routine", "normal"]

    has_high = any(cue in text for cue in high_cues)
    has_moderate = any(cue in text for cue in moderate_cues)
    has_low = any(cue in text for cue in low_cues)

    if "toxic" in label or "ineffective" in label:
        expected = "high"
    elif "adjust" in label:
        expected = "moderate"
    elif "safe" in label:
        expected = "low"
    else:
        expected = "unknown"

    base = 0.75
    if expected == "high":
        base = 0.92 if has_high else (0.35 if has_low else 0.65)
    elif expected == "moderate":
        base = 0.90 if has_moderate else (0.45 if has_high and not has_moderate else 0.65)
    elif expected == "low":
        base = 0.92 if has_low else (0.35 if has_high else 0.65)

    llm_conf = explanation.get("llm_confidence_percent")
    if isinstance(llm_conf, (int, float)):
        base = (0.70 * base) + (0.30 * _clamp(float(llm_conf) / 100.0))

    return _clamp(base)


def compute_hybrid_confidence(
    variants: List[Dict[str, Any]],
    cpic_level: Optional[str],
    risk_label: Optional[str],
    explanation: Optional[Dict[str, Any]] = None,
) -> Tuple[float, Dict[str, float]]:
    q_vcf = compute_vcf_quality_score(variants)
    g_cpic = compute_cpic_guideline_score(cpic_level)
    p_llm = compute_llm_consistency_score(risk_label, explanation)

    final = _clamp((W1 * q_vcf) + (W2 * g_cpic) + (W3 * p_llm))
    return round(final, 2), {
        "q_vcf": round(q_vcf, 3),
        "g_cpic": round(g_cpic, 3),
        "p_llm": round(p_llm, 3),
    }
