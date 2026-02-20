"""
Clinical Risk Engine for PharmaGuard
RIFT 2026 Hackathon - Complete CPIC-aligned rules for all drugs
"""

from typing import List, Dict, Any
from parser import get_variants_by_gene, get_diplotype, get_phenotype

# CPIC guideline references
CPIC_GUIDELINES = {
    "CODEINE": "CPIC Guideline for Codeine and CYP2D6 (Level A)",
    "WARFARIN": "CPIC Guideline for Warfarin and CYP2C9/VKORC1 (Level A)",
    "CLOPIDOGREL": "CPIC Guideline for Clopidogrel and CYP2C19 (Level A)",
    "SIMVASTATIN": "CPIC Guideline for Simvastatin and SLCO1B1 (Level A)",
    "AZATHIOPRINE": "CPIC Guideline for Azathioprine and TPMT (Level A)",
    "FLUOROURACIL": "CPIC Guideline for Fluorouracil and DPYD (Level A)",
    "FLUOXETINE": "CPIC Guideline for Fluoxetine and CYP2D6 (Level A)",
    "PAROXETINE": "CPIC Guideline for Paroxetine and CYP2D6 (Level A)",
    "RISPERIDONE": "CPIC Guideline for Risperidone and CYP2D6 (Level A)",
    "IBUPROFEN": "CPIC Guideline for Ibuprofen and CYP2C9 (Level B)",
    "OMEPRAZOLE": "CPIC Guideline for Omeprazole and CYP2C19 (Level A)",
}

def get_clinical_risk(variants: List[Dict], drug: str) -> Dict[str, Any]:
    """
    Determine clinical risk for a specific drug based on genetic variants.
    Returns complete risk assessment matching JSON schema.
    """
    drug = drug.upper().strip()
    
    # Default response (no variants found)
    default_response = {
        "label": "Unknown",
        "severity": "unknown",
        "phenotype": "Unknown",
        "diplotype": "*1/*1",
        "gene": "Unknown",
        "recommendation": "Insufficient genetic data. Standard dosing recommended with clinical monitoring.",
        "confidence_score": 0.5,
        "cpic_level": "N/A"
    }
    
    # Route to appropriate drug-specific function
    if drug == "CODEINE":
        return analyze_codeine(variants)
    elif drug == "WARFARIN":
        return analyze_warfarin(variants)
    elif drug == "CLOPIDOGREL":
        return analyze_clopidogrel(variants)
    elif drug == "SIMVASTATIN":
        return analyze_simvastatin(variants)
    elif drug == "AZATHIOPRINE":
        return analyze_azathioprine(variants)
    elif drug == "FLUOROURACIL":
        return analyze_fluorouracil(variants)
    elif drug == "FLUOXETINE":
        return analyze_fluoxetine(variants)
    elif drug == "PAROXETINE":
        return analyze_paroxetine(variants)
    elif drug == "RISPERIDONE":
        return analyze_risperidone(variants)
    elif drug == "IBUPROFEN":
        return analyze_ibuprofen(variants)
    elif drug == "OMEPRAZOLE":
        return analyze_omeprazole(variants)
    else:
        return default_response

def analyze_codeine(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2D6-guided codeine analysis"""
    gene = "CYP2D6"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    # Default response
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use codeine with standard dosing.",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    # Check for poor metabolizers
    if phenotype == "PM":
        result.update({
            "label": "Toxic",
            "severity": "high",
            "recommendation": "AVOID codeine. Poor metabolizers risk morphine toxicity. Use non-opioid analgesics or alternative opioids not dependent on CYP2D6 (e.g., morphine, hydromorphone).",
            "confidence_score": 0.95
        })
    # Check for ultra-rapid metabolizers
    elif phenotype == "RM" or phenotype == "URM" or phenotype == "UM":
        result.update({
            "label": "Toxic",
            "severity": "high",
            "recommendation": "AVOID codeine. Ultra-rapid metabolizers have increased risk of life-threatening respiratory depression from rapid morphine formation. Use alternative analgesics.",
            "confidence_score": 0.95
        })
    
    return result

def analyze_fluoxetine(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2D6-guided fluoxetine (Prozac) analysis"""
    gene = "CYP2D6"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use fluoxetine at standard dose (20mg/day). Monitor for side effects.",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    if phenotype == "PM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "high",
            "recommendation": "REDUCE fluoxetine dose. Poor metabolizers have 2-4x higher drug concentrations. Start at 10mg/day and titrate slowly. Consider alternative antidepressant not metabolized by CYP2D6 (e.g., citalopram, sertraline).",
            "confidence_score": 0.95
        })
    elif phenotype == "IM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "moderate",
            "recommendation": "CONSIDER LOWER fluoxetine dose. Intermediate metabolizers may have higher drug levels. Start at 10-15mg/day and monitor for side effects.",
            "confidence_score": 0.90
        })
    
    return result

def analyze_paroxetine(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2D6-guided paroxetine (Paxil) analysis"""
    gene = "CYP2D6"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use paroxetine at standard dose (20mg/day).",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    if phenotype == "PM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "high",
            "recommendation": "REDUCE paroxetine dose. Poor metabolizers have significantly higher drug concentrations and increased risk of side effects. Start at 10mg/day or consider alternative antidepressant not metabolized by CYP2D6.",
            "confidence_score": 0.95
        })
    elif phenotype == "IM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "moderate",
            "recommendation": "CONSIDER LOWER paroxetine dose. Intermediate metabolizers may have elevated drug levels. Start at 10-15mg/day and monitor for side effects.",
            "confidence_score": 0.90
        })
    
    return result

def analyze_risperidone(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2D6-guided risperidone (Risperdal) analysis"""
    gene = "CYP2D6"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use risperidone at standard dose (2-6mg/day).",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    if phenotype == "PM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "high",
            "recommendation": "REDUCE risperidone dose. Poor metabolizers have higher active fraction concentrations. Start at 0.5-1mg/day and titrate slowly. Monitor for extrapyramidal side effects.",
            "confidence_score": 0.95
        })
    
    return result

def analyze_warfarin(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2C9-guided warfarin analysis"""
    gene = "CYP2C9"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    # Check for VKORC1 variant (important for warfarin)
    vkorc1_variants = [v for v in variants if v["gene"] == "VKORC1" or v["rsid"] == "rs9923231"]
    vkorc1_present = len(vkorc1_variants) > 0
    
    result = {
        "label": "Adjust Dosage",
        "severity": "moderate",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Start with standard warfarin dosing (5mg/day). Monitor INR closely.",
        "confidence_score": 0.80,
        "cpic_level": "A"
    }
    
    if phenotype == "PM" or "*2/*3" in diplotype or "*3/*3" in diplotype:
        result.update({
            "label": "Adjust Dosage",
            "severity": "high",
            "recommendation": "SIGNIFICANTLY REDUCE warfarin dose. CYP2C9 poor metabolizers require 30-50% lower starting doses. Use pharmacogenetic dosing algorithms. Monitor INR frequently.",
            "confidence_score": 0.95
        })
    elif phenotype == "IM" or "*1/*2" in diplotype or "*1/*3" in diplotype or "*2/*2" in diplotype:
        result.update({
            "label": "Adjust Dosage",
            "severity": "moderate",
            "recommendation": "REDUCE warfarin dose. CYP2C9 intermediate metabolizers require 20-30% lower starting doses. Monitor INR closely.",
            "confidence_score": 0.90
        })
    
    if vkorc1_present:
        result["recommendation"] += " VKORC1 variant detected - consider 40-50% dose reduction."
    
    return result

def analyze_ibuprofen(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2C9-guided ibuprofen analysis"""
    gene = "CYP2C9"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use ibuprofen at standard OTC doses (200-400mg every 6 hours).",
        "confidence_score": 0.80,
        "cpic_level": "B"
    }
    
    if phenotype == "PM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "moderate",
            "recommendation": "CONSIDER LOWER ibuprofen dose or alternative. Poor metabolizers may have increased risk of GI bleeding with chronic use. Use lowest effective dose for shortest duration.",
            "confidence_score": 0.85
        })
    
    return result

def analyze_clopidogrel(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2C19-guided clopidogrel analysis"""
    gene = "CYP2C19"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    # Debug print (remove after testing)
    print(f"Clopidogrel Debug: diplotype={diplotype}, phenotype={phenotype}")
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use clopidogrel at standard dose (75mg/day).",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    # Check for loss of function variants
    if phenotype == "PM":
        result.update({
            "label": "Ineffective",
            "severity": "high",
            "recommendation": "AVOID clopidogrel. Poor metabolizers have significantly reduced active metabolite formation. Use alternative antiplatelet therapy: prasugrel or ticagrelor at standard doses.",
            "confidence_score": 0.95
        })
    elif phenotype == "IM":
        result.update({
            "label": "Ineffective",
            "severity": "moderate",
            "recommendation": "CONSIDER ALTERNATIVE to clopidogrel. Intermediate metabolizers have reduced platelet inhibition. Prasugrel or ticagrelor may be more effective.",
            "confidence_score": 0.85
        })
    elif phenotype == "RM" or phenotype == "UM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "low",
            "recommendation": "Rapid/ultrarapid metabolizers may have slightly increased active metabolite formation and bleeding risk. Standard dosing is likely appropriate with monitoring.",
            "confidence_score": 0.80
        })
    
    return result

def analyze_omeprazole(variants: List[Dict]) -> Dict[str, Any]:
    """CYP2C19-guided omeprazole (Prilosec) analysis"""
    gene = "CYP2C19"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    phenotype = get_phenotype(gene, diplotype)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": phenotype,
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use omeprazole at standard dose (20mg/day).",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    if phenotype == "RM" or phenotype == "UM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "moderate",
            "recommendation": "CONSIDER INCREASED omeprazole dose. Rapid/ultrarapid metabolizers may have reduced drug exposure and therapeutic failure. Consider 40mg/day or alternative PPI less affected by CYP2C19 (e.g., rabeprazole).",
            "confidence_score": 0.90
        })
    elif phenotype == "PM":
        result.update({
            "label": "Adjust Dosage",
            "severity": "low",
            "recommendation": "CONSIDER LOWER omeprazole dose. Poor metabolizers have 5-10x higher drug exposure. Standard doses may be effective at lower amounts. Monitor for efficacy.",
            "confidence_score": 0.90
        })
    
    return result

def analyze_simvastatin(variants: List[Dict]) -> Dict[str, Any]:
    """SLCO1B1-guided simvastatin analysis"""
    gene = "SLCO1B1"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    
    # Check for *5 variant (rs4149056)
    c521t_variants = [v for v in gene_variants if v["allele"] == "*5" or v["rsid"] == "rs4149056"]
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": "Normal function",
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use simvastatin at standard dose (up to 40mg/day).",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    if c521t_variants:
        for v in c521t_variants:
            if v["genotype"] in ["1/1", "1|1"]:  # Homozygous
                result.update({
                    "label": "Toxic",
                    "severity": "high",
                    "phenotype": "Poor function",
                    "recommendation": "SIGNIFICANTLY REDUCE simvastatin dose or consider alternative statin. Homozygous SLCO1B1 variants have 200% higher statin exposure. Maximum recommended dose: 20mg/day with close monitoring for myopathy.",
                    "confidence_score": 0.95
                })
                break
            elif v["genotype"] in ["0/1", "1/0", "0|1", "1|0"]:  # Heterozygous
                result.update({
                    "label": "Adjust Dosage",
                    "severity": "moderate",
                    "phenotype": "Intermediate function",
                    "recommendation": "REDUCE simvastatin dose. Heterozygous SLCO1B1 variants have increased statin exposure. Maximum recommended dose: 40mg/day. Consider alternative statin (pravastatin, rosuvastatin) if higher doses needed.",
                    "confidence_score": 0.90
                })
                break
    
    return result

def analyze_azathioprine(variants: List[Dict]) -> Dict[str, Any]:
    """TPMT-guided azathioprine analysis"""
    gene = "TPMT"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": "Normal metabolizer",
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use azathioprine at standard dose (2-3 mg/kg/day).",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    # Count variant alleles
    variant_count = 0
    for v in gene_variants:
        if v["genotype"] in ["1/1", "1|1"]:
            variant_count += 2
        elif v["genotype"] in ["0/1", "1/0", "0|1", "1|0"]:
            variant_count += 1
    
    if variant_count == 2:  # Two variant alleles
        result.update({
            "label": "Toxic",
            "severity": "critical",
            "phenotype": "Poor metabolizer",
            "recommendation": "AVOID azathioprine. TPMT poor metabolizers risk life-threatening myelosuppression. Use alternative immunosuppressants (e.g., cyclosporine, tacrolimus) or reduce dose by 90% with extreme caution and frequent monitoring.",
            "confidence_score": 0.98
        })
    elif variant_count == 1:  # One variant allele
        result.update({
            "label": "Adjust Dosage",
            "severity": "high",
            "phenotype": "Intermediate metabolizer",
            "recommendation": "REDUCE azathioprine dose. TPMT intermediate metabolizers require 30-70% dose reduction. Start at 30-50% of standard dose and titrate based on tolerance and blood counts.",
            "confidence_score": 0.90
        })
    
    return result

def analyze_fluorouracil(variants: List[Dict]) -> Dict[str, Any]:
    """DPYD-guided fluorouracil analysis"""
    gene = "DPYD"
    gene_variants = get_variants_by_gene(variants, gene)
    diplotype = get_diplotype(variants, gene)
    
    result = {
        "label": "Safe",
        "severity": "none",
        "phenotype": "Normal metabolizer",
        "diplotype": diplotype,
        "gene": gene,
        "recommendation": "Use fluorouracil at standard dose.",
        "confidence_score": 0.85,
        "cpic_level": "A"
    }
    
    # Check for DPYD variants
    high_risk_variants = ["*2A", "*13", "HapB3"]
    
    for v in gene_variants:
        if v["allele"] in high_risk_variants or v["function"] == "Loss of function":
            if v["genotype"] in ["1/1", "1|1"]:  # Homozygous
                result.update({
                    "label": "Toxic",
                    "severity": "critical",
                    "phenotype": "Poor metabolizer",
                    "recommendation": "AVOID fluorouracil. DPYD poor metabolizers risk severe, life-threatening toxicity including myelosuppression, neurotoxicity, and gastrointestinal toxicity. Use alternative chemotherapeutic agents.",
                    "confidence_score": 0.98
                })
                break
            elif v["genotype"] in ["0/1", "1/0", "0|1", "1|0"]:  # Heterozygous
                result.update({
                    "label": "Toxic",
                    "severity": "high",
                    "phenotype": "Intermediate metabolizer",
                    "recommendation": "REDUCE fluorouracil dose by 50%. DPYD intermediate metabolizers have increased risk of severe toxicity. Consider alternative chemotherapy or reduce dose with intensive monitoring.",
                    "confidence_score": 0.95
                })
                break
    
    return result