from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback
import datetime
import uuid
from typing import List, Optional, Dict, Tuple
from parser import parse_vcf_file, TARGET_VARIANTS, DRUG_GENE_MAP
from engine import get_clinical_risk, CPIC_GUIDELINES
from llm import get_explanation, get_llm_clinical_risk, is_llm_configured
from confidence import compute_hybrid_confidence, confidence_model_config

app = FastAPI(title="PharmaGuard API", description="Pharmacogenomic Risk Prediction System", version="2.0")

if not is_llm_configured():
    print("WARNING: LLM API key not configured. Set OPENAI_API_KEY. Falling back to rule engine/explanation fallback.")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def normalize_vcf_path(raw_path: Optional[str]) -> Optional[str]:
    """Normalize path strings like @\"C:\\data\\file.vcf\" into a usable file path."""
    if not raw_path:
        return None

    path = raw_path.strip()
    if not path:
        return None

    if path.startswith('@'):
        path = path[1:].lstrip()

    if len(path) >= 2 and path[0] == path[-1] and path[0] in ('"', "'"):
        path = path[1:-1]

    return os.path.expandvars(os.path.expanduser(path))

async def resolve_vcf_input(
    vcf: Optional[UploadFile],
    vcf_path: Optional[str]
) -> Tuple[str, str, int, bool]:
    """
    Resolve VCF from either multipart upload or local file path.
    Returns: (file_path, file_name, file_size_bytes, should_delete_after_use)
    """
    normalized_path = normalize_vcf_path(vcf_path)

    if vcf and normalized_path:
        raise HTTPException(status_code=400, detail="Provide either 'vcf' upload or 'vcf_path', not both")

    if vcf:
        if not vcf.filename or not vcf.filename.lower().endswith('.vcf'):
            raise HTTPException(status_code=400, detail="File must be a .vcf file")

        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{vcf.filename}")
        try:
            content = await vcf.read()
            if len(content) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            return file_path, vcf.filename, len(content), True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    if normalized_path:
        if not normalized_path.lower().endswith('.vcf'):
            raise HTTPException(status_code=400, detail="vcf_path must point to a .vcf file")
        if not os.path.isfile(normalized_path):
            raise HTTPException(status_code=400, detail=f"VCF file not found at path: {normalized_path}")

        file_size = os.path.getsize(normalized_path)
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        return normalized_path, os.path.basename(normalized_path), file_size, False

    raise HTTPException(status_code=400, detail="Provide a VCF via upload field 'vcf' or form field 'vcf_path'")

# Extended drug-gene map for polypharmacy detection
EXTENDED_DRUG_GENE_MAP = {
    "CODEINE": ["CYP2D6"],
    "WARFARIN": ["CYP2C9", "VKORC1"],
    "CLOPIDOGREL": ["CYP2C19"],
    "SIMVASTATIN": ["SLCO1B1"],
    "AZATHIOPRINE": ["TPMT"],
    "FLUOROURACIL": ["DPYD"],
    "FLUOXETINE": ["CYP2D6"],  # Prozac
    "PAROXETINE": ["CYP2D6"],   # Paxil
    "RISPERIDONE": ["CYP2D6"],   # Risperdal
    "TAMOXIFEN": ["CYP2D6"],     # Breast cancer drug
    "OMEPRAZOLE": ["CYP2C19"],    # Prilosec
    "PHENYTOIN": ["CYP2C9"],      # Dilantin
    "IBUPROFEN": ["CYP2C9"],      # Advil
    "DICLOFENAC": ["CYP2C9"],     # Voltaren
}

CPIC_FALLBACK_ACTIONS = {
    "CODEINE": "CPIC-guided action: avoid codeine in poor/ultrarapid CYP2D6 metabolizers; otherwise use standard dosing with monitoring.",
    "WARFARIN": "CPIC-guided action: use genotype-informed initial dosing and monitor INR closely, with dose reduction for reduced-function CYP2C9/VKORC1 variants.",
    "CLOPIDOGREL": "CPIC-guided action: consider alternative antiplatelet therapy in CYP2C19 loss-of-function phenotypes; standard dosing otherwise.",
    "SIMVASTATIN": "CPIC-guided action: reduce simvastatin dose or consider alternative statin for decreased-function SLCO1B1 phenotypes.",
    "AZATHIOPRINE": "CPIC-guided action: reduce dose substantially for intermediate TPMT activity and avoid/near-avoid in poor metabolizers.",
    "FLUOROURACIL": "CPIC-guided action: major dose reduction or alternative therapy for reduced-function DPYD phenotypes.",
    "FLUOXETINE": "CPIC-guided action: consider lower starting dose with CYP2D6 poor/intermediate metabolizer phenotypes.",
    "PAROXETINE": "CPIC-guided action: consider lower starting dose with CYP2D6 poor/intermediate metabolizer phenotypes.",
    "RISPERIDONE": "CPIC-guided action: consider lower starting dose and slow titration in CYP2D6 poor metabolizers.",
    "IBUPROFEN": "CPIC-guided action: consider lower dose/monitoring in reduced-function CYP2C9 phenotypes.",
    "OMEPRAZOLE": "CPIC-guided action: consider dose increase for rapid CYP2C19 metabolizers and dose reduction for poor metabolizers.",
}

def ensure_recommendation_text(drug: str, primary: Optional[str], secondary: Optional[str]) -> str:
    first = (primary or "").strip()
    if first:
        return first
    second = (secondary or "").strip()
    if second:
        return second
    return CPIC_FALLBACK_ACTIONS.get(
        drug.upper(),
        "CPIC-guided dosing recommendation unavailable from source response; perform clinician-reviewed pharmacogenomic assessment."
    )

def normalize_phenotype_code(phenotype: Optional[str]) -> str:
    """Normalize phenotype labels to schema-compliant abbreviations."""
    if not phenotype:
        return "Unknown"
    normalized = phenotype.strip().lower()
    phenotype_map = {
        "poor metabolizer": "PM",
        "pm": "PM",
        "intermediate metabolizer": "IM",
        "im": "IM",
        "normal metabolizer": "NM",
        "nm": "NM",
        "rapid metabolizer": "RM",
        "rm": "RM",
        "ultrarapid metabolizer": "URM",
        "ultra-rapid metabolizer": "URM",
        "urm": "URM",
        "um": "URM",
    }
    return phenotype_map.get(normalized, "Unknown")

@app.get("/")
async def root():
    return {
        "service": "PharmaGuard API",
        "version": "2.0",
        "status": "operational",
        "llm_api_key_configured": is_llm_configured(),
        "supported_drugs": list(DRUG_GENE_MAP.keys()),
        "supported_genes": list(set([v["gene"] for v in TARGET_VARIANTS.values()])),
        "cpic_guidelines": CPIC_GUIDELINES
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "llm_api_key_configured": is_llm_configured()
    }

def detect_bottlenecks(drugs: List[str], variants: List[dict]) -> List[Dict]:
    """
    Detect polypharmacy bottlenecks when multiple drugs compete for same enzyme
    """
    # Count drugs per gene
    gene_counts = {}
    drug_gene_map = {}
    
    for drug in drugs:
        drug_upper = drug.upper()
        genes = EXTENDED_DRUG_GENE_MAP.get(drug_upper, [])
        drug_gene_map[drug_upper] = genes
        for gene in genes:
            gene_counts[gene] = gene_counts.get(gene, 0) + 1
    
    # Get patient's phenotype for each gene
    gene_phenotypes = {}
    for v in variants:
        gene = v.get("gene")
        if gene and gene not in gene_phenotypes:
            # Simplified phenotype extraction - in production, use engine logic
            if v.get("genotype") in ["1/1", "1|1"]:
                gene_phenotypes[gene] = "Poor metabolizer"
            elif v.get("genotype") in ["0/1", "1/0", "0|1", "1|0"]:
                gene_phenotypes[gene] = "Intermediate metabolizer"
            else:
                gene_phenotypes[gene] = "Normal metabolizer"
    
    # Generate warnings for genes with multiple drugs
    warnings = []
    for gene, count in gene_counts.items():
        if count >= 2:
            # Find which drugs are competing
            competing_drugs = [
                drug for drug in drugs 
                if gene in drug_gene_map.get(drug.upper(), [])
            ]
            
            # Get patient's phenotype for this gene
            phenotype = gene_phenotypes.get(gene, "Unknown")
            
            # Determine severity based on count and phenotype
            severity = "moderate"
            risk_level = "medium"
            
            if count >= 3:
                severity = "critical"
                risk_level = "high"
            elif count >= 2 and phenotype in ["Poor metabolizer", "Intermediate metabolizer"]:
                severity = "high"
                risk_level = "high"
            elif count >= 2:
                severity = "moderate"
                risk_level = "medium"
            
            # Clinical note based on severity
            clinical_notes = {
                "critical": f"CRITICAL: {count} drugs competing for {gene}. This creates a severe metabolic bottleneck even in normal metabolizers. Consider alternative therapies.",
                "high": f"HIGH RISK: Multiple drugs ({count}) utilizing {gene}. Patient's {phenotype} status compounds this risk. Monitor closely.",
                "moderate": f"MODERATE RISK: {count} drugs competing for {gene}. May reduce metabolic capacity. Consider monitoring drug levels."
            }
            
            warnings.append({
                "gene": gene,
                "competing_drugs": competing_drugs,
                "count": count,
                "severity": severity,
                "risk_level": risk_level,
                "patient_phenotype": phenotype,
                "warning": f"Metabolic bottleneck detected: {count} drugs competing for {gene} enzyme",
                "clinical_note": clinical_notes.get(severity, "")
            })
    
    return warnings

@app.post("/analyze")
async def analyze(
    drug: str = Form(...),
    vcf: Optional[UploadFile] = File(None),
    vcf_path: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None)
):
    """
    Analyze VCF file for pharmacogenomic risk associated with a specific drug.
    Returns complete JSON schema as required by RIFT 2026.
    """
    try:
        # Generate patient ID if not provided
        if not patient_id:
            patient_id = f"PATIENT_{uuid.uuid4().hex[:8].upper()}"

        file_path, source_file_name, source_file_size, should_cleanup = await resolve_vcf_input(vcf, vcf_path)

        # Step 1: Parse VCF file
        try:
            variants = parse_vcf_file(file_path)
            parsing_success = True
            variants_count = len(variants)
        except Exception as e:
            variants = []
            parsing_success = False
            variants_count = 0
            print(f"Parsing error: {traceback.format_exc()}")

        # Step 2: Get clinical risk assessment
        try:
            risk = get_llm_clinical_risk(drug, variants)
        except Exception as e:
            # Safety fallback: deterministic CPIC rules if LLM fails.
            risk = get_clinical_risk(variants, drug)
            print(f"Risk engine error: {traceback.format_exc()}")

        # Step 3: Get LLM explanation
        try:
            explanation = get_explanation(drug, risk['phenotype'], variants)
        except Exception as e:
            explanation = {
                "summary": f"Patient exhibits {risk['phenotype']} phenotype for {drug}.",
                "mechanism": "LLM explanation temporarily unavailable. Please refer to CPIC guidelines."
            }
            print(f"LLM error: {traceback.format_exc()}")

        # Step 4: Guarantee recommendation text + compute deterministic hybrid confidence score
        resolved_recommendation = ensure_recommendation_text(
            drug=drug,
            primary=explanation.get("recommendation") if isinstance(explanation, dict) else None,
            secondary=risk.get("recommendation")
        )
        risk["recommendation"] = resolved_recommendation
        if isinstance(explanation, dict):
            explanation["recommendation"] = resolved_recommendation

        confidence_score, confidence_breakdown = compute_hybrid_confidence(
            variants=variants,
            cpic_level=risk.get("cpic_level"),
            risk_label=risk.get("label"),
            explanation=explanation
        )
        risk["confidence_score"] = confidence_score

        # Step 5: Clean up uploaded file (privacy first!)
        if should_cleanup:
            try:
                os.remove(file_path)
            except:
                pass

        primary_gene = risk.get("gene")
        filtered_variants = [
            {"rsid": v["rsid"]}
            for v in variants
            if primary_gene and v.get("gene") == primary_gene and v.get("rsid")
        ]

        # Step 6: Build complete JSON response matching required schema
        response = {
            "patient_id": patient_id,
            "drug": drug.upper(),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "risk_assessment": {
                "risk_label": risk.get("label"),
                "confidence_score": risk.get("confidence_score"),
                "severity": risk.get("severity")
            },
            "pharmacogenomic_profile": {
                "primary_gene": primary_gene,
                "diplotype": risk.get("diplotype"),
                "phenotype": normalize_phenotype_code(risk.get("phenotype")),
                "detected_variants": filtered_variants
            },
            "clinical_recommendation": {
                "recommendation_text": resolved_recommendation
            },
            "llm_generated_explanation": {
                "summary": explanation.get("summary", ""),
                "mechanism": explanation.get("mechanism", "")
            },
            "quality_metrics": {
                "vcf_parsing_success": parsing_success,
                "total_variants_analyzed": variants_count,
                "file_name": source_file_name,
                "file_size_bytes": source_file_size,
                "confidence_model": confidence_model_config(),
                "data_retention": "Zero-retention - File purged after processing"
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        print("CRITICAL ERROR IN API:")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(e),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        )

async def get_comprehensive_risk(variants: List[dict], primary_drug: str) -> dict:
    """
    Generate risk assessment for all 6 drugs (full panel screening)
    """
    all_drugs = ["CODEINE", "WARFARIN", "CLOPIDOGREL", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"]
    panel = {}
    
    for drug in all_drugs:
        if drug == primary_drug.upper():
            continue
        
        try:
            risk = get_llm_clinical_risk(drug, variants)
            confidence_score, _ = compute_hybrid_confidence(
                variants=variants,
                cpic_level=risk.get("cpic_level"),
                risk_label=risk.get("label"),
                explanation=None
            )
            panel[drug] = {
                "risk_label": risk.get("label", "Unknown"),
                "severity": risk.get("severity", "unknown"),
                "gene": risk.get("gene", "Unknown"),
                "phenotype": risk.get("phenotype", "Unknown"),
                "confidence_score": confidence_score
            }
        except:
            # Safety fallback: deterministic CPIC rules if LLM fails.
            risk = get_clinical_risk(variants, drug)
            confidence_score, _ = compute_hybrid_confidence(
                variants=variants,
                cpic_level=risk.get("cpic_level"),
                risk_label=risk.get("label"),
                explanation=None
            )
            panel[drug] = {
                "risk_label": risk.get("label", "Unknown"),
                "severity": risk.get("severity", "unknown"),
                "gene": risk.get("gene", "Unknown"),
                "phenotype": risk.get("phenotype", "Unknown"),
                "confidence_score": confidence_score
            }
    
    return panel

@app.post("/analyze/batch")
async def analyze_batch(
    drugs: str = Form(...),
    vcf: Optional[UploadFile] = File(None),
    vcf_path: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None)
):
    """
    Analyze multiple drugs at once (comma-separated)
    Includes polypharmacy bottleneck detection
    """
    try:
        # Parse drug list
        drug_list = [d.strip().upper() for d in drugs.split(',') if d.strip()]
        if not drug_list:
            raise HTTPException(status_code=400, detail="Provide at least one drug in 'drugs'")

        # Generate patient ID if not provided
        if not patient_id:
            patient_id = f"PATIENT_{uuid.uuid4().hex[:8].upper()}"

        file_path, source_file_name, source_file_size, should_cleanup = await resolve_vcf_input(vcf, vcf_path)
        try:
            # Parse variants
            try:
                variants = parse_vcf_file(file_path)
                parsing_success = True
                variants_count = len(variants)
            except Exception:
                variants = []
                parsing_success = False
                variants_count = 0

            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            response_items = []

            # Analyze each drug and return strict per-drug schema objects
            for drug in drug_list:
                try:
                    risk = get_llm_clinical_risk(drug, variants)
                except Exception:
                    risk = get_clinical_risk(variants, drug)

                try:
                    explanation = get_explanation(drug, risk.get("phenotype", "Unknown"), variants)
                except Exception:
                    explanation = {
                        "summary": f"Patient exhibits {risk.get('phenotype', 'Unknown')} phenotype for {drug}.",
                        "mechanism": "LLM explanation temporarily unavailable. Please refer to CPIC guidelines."
                    }

                resolved_recommendation = ensure_recommendation_text(
                    drug=drug,
                    primary=explanation.get("recommendation") if isinstance(explanation, dict) else None,
                    secondary=risk.get("recommendation")
                )
                risk["recommendation"] = resolved_recommendation

                confidence_score, _ = compute_hybrid_confidence(
                    variants=variants,
                    cpic_level=risk.get("cpic_level"),
                    risk_label=risk.get("label"),
                    explanation=explanation
                )

                primary_gene = risk.get("gene")
                filtered_variants = [
                    {"rsid": v["rsid"]}
                    for v in variants
                    if primary_gene and v.get("gene") == primary_gene and v.get("rsid")
                ]

                response_items.append({
                    "patient_id": patient_id,
                    "drug": drug,
                    "timestamp": timestamp,
                    "risk_assessment": {
                        "risk_label": risk.get("label"),
                        "confidence_score": confidence_score,
                        "severity": risk.get("severity")
                    },
                    "pharmacogenomic_profile": {
                        "primary_gene": primary_gene,
                        "diplotype": risk.get("diplotype"),
                        "phenotype": normalize_phenotype_code(risk.get("phenotype")),
                        "detected_variants": filtered_variants
                    },
                    "clinical_recommendation": {
                        "recommendation_text": resolved_recommendation
                    },
                    "llm_generated_explanation": {
                        "summary": explanation.get("summary", ""),
                        "mechanism": explanation.get("mechanism", "")
                    },
                    "quality_metrics": {
                        "vcf_parsing_success": parsing_success,
                        "total_variants_analyzed": variants_count,
                        "file_name": source_file_name,
                        "file_size_bytes": source_file_size,
                        "confidence_model": confidence_model_config(),
                        "data_retention": "Zero-retention - File purged after processing"
                    }
                })

            return response_items
        finally:
            # Clean up (privacy first!)
            if should_cleanup:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
