"""
Pure Python VCF Parser for PharmaGuard
RIFT 2026 Hackathon - Compliant with 6 genes requirement
"""

import re
from typing import List, Dict, Any

# Complete mapping of all target variants for 6 genes
TARGET_VARIANTS = {
    # CYP2D6 (Codeine, Tamoxifen)
    "rs1065852": {"gene": "CYP2D6", "allele": "*4", "function": "Poor metabolizer", "cpic_level": "A"},
    "rs3892097": {"gene": "CYP2D6", "allele": "*4", "function": "Poor metabolizer", "cpic_level": "A"},
    "rs5030655": {"gene": "CYP2D6", "allele": "*6", "function": "Poor metabolizer", "cpic_level": "A"},
    "rs5030865": {"gene": "CYP2D6", "allele": "*3", "function": "Poor metabolizer", "cpic_level": "A"},
    
    # CYP2C19 (Clopidogrel, Voriconazole)
    "rs4244285": {"gene": "CYP2C19", "allele": "*2", "function": "Loss of function", "cpic_level": "A"},
    "rs4986893": {"gene": "CYP2C19", "allele": "*3", "function": "Loss of function", "cpic_level": "A"},
    "rs12248560": {"gene": "CYP2C19", "allele": "*17", "function": "Gain of function", "cpic_level": "A"},
    
    # CYP2C9 (Warfarin, Phenytoin)
    "rs1799853": {"gene": "CYP2C9", "allele": "*2", "function": "Reduced function", "cpic_level": "A"},
    "rs1057910": {"gene": "CYP2C9", "allele": "*3", "function": "Reduced function", "cpic_level": "A"},
    "rs28371686": {"gene": "CYP2C9", "allele": "*5", "function": "Reduced function", "cpic_level": "A"},
    "rs9332131": {"gene": "CYP2C9", "allele": "*6", "function": "Reduced function", "cpic_level": "A"},
    
    # SLCO1B1 (Simvastatin)
    "rs4149056": {"gene": "SLCO1B1", "allele": "*5", "function": "Reduced function", "cpic_level": "A"},
    "rs2306283": {"gene": "SLCO1B1", "allele": "*1b", "function": "Normal function", "cpic_level": "A"},
    
    # TPMT (Azathioprine, Mercaptopurine)
    "rs1800462": {"gene": "TPMT", "allele": "*2", "function": "Loss of function", "cpic_level": "A"},
    "rs1800460": {"gene": "TPMT", "allele": "*3B", "function": "Loss of function", "cpic_level": "A"},
    "rs1142345": {"gene": "TPMT", "allele": "*3C", "function": "Loss of function", "cpic_level": "A"},
    
    # DPYD (Fluorouracil, Capecitabine)
    "rs3918290": {"gene": "DPYD", "allele": "*2A", "function": "Loss of function", "cpic_level": "A"},
    "rs55886062": {"gene": "DPYD", "allele": "*13", "function": "Loss of function", "cpic_level": "A"},
    "rs67376798": {"gene": "DPYD", "allele": "*9B", "function": "Reduced function", "cpic_level": "A"},
    "rs75017182": {"gene": "DPYD", "allele": "HapB3", "function": "Reduced function", "cpic_level": "A"},
}

# Drug-to-gene mapping
DRUG_GENE_MAP = {
    "CODEINE": ["CYP2D6"],
    "WARFARIN": ["CYP2C9", "VKORC1"],
    "CLOPIDOGREL": ["CYP2C19"],
    "SIMVASTATIN": ["SLCO1B1"],
    "AZATHIOPRINE": ["TPMT"],
    "FLUOROURACIL": ["DPYD"],
    "FLUOXETINE": ["CYP2D6"],
    "PAROXETINE": ["CYP2D6"],
    "RISPERIDONE": ["CYP2D6"],
    "IBUPROFEN": ["CYP2C9"],
    "OMEPRAZOLE": ["CYP2C19"],
}

def parse_vcf_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Parse VCF file and extract pharmacogenomic variants.
    Pure Python implementation - no external dependencies.
    """
    detected_variants = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                # Skip header lines
                if line.startswith('#'):
                    continue
                
                # Parse VCF columns
                cols = line.strip().split('\t')
                if len(cols) < 8:
                    continue
                
                chrom = cols[0]
                pos = cols[1]
                rsid = cols[2]
                ref = cols[3]
                alt = cols[4]
                qual = cols[5]
                filt = cols[6]
                info = cols[7]
                fmt = cols[8] if len(cols) >= 9 else ""
                
                # Check if this is a target variant
                if rsid in TARGET_VARIANTS:
                    variant_info = TARGET_VARIANTS[rsid]
                    
                    # Extract genotype if sample data exists
                    genotype = "./."
                    sample_dp = None
                    if len(cols) >= 10:
                        sample_data = cols[9]
                        gt_field = sample_data.split(':')[0] if ':' in sample_data else sample_data
                        genotype = gt_field
                        # Try to parse read depth from FORMAT/sample columns
                        if fmt and ":" in sample_data:
                            fmt_fields = fmt.split(":")
                            sample_fields = sample_data.split(":")
                            if "DP" in fmt_fields:
                                dp_index = fmt_fields.index("DP")
                                if dp_index < len(sample_fields):
                                    try:
                                        sample_dp = int(sample_fields[dp_index])
                                    except Exception:
                                        sample_dp = None
                    
                    # Extract additional info from INFO field
                    gene = variant_info["gene"]
                    allele = variant_info["allele"]
                    function = variant_info["function"]
                    
                    # Try to get gene from INFO if available
                    gene_match = re.search(r'GENE=([^;]+)', info)
                    has_gene_annotation = bool(gene_match)
                    if gene_match:
                        gene = gene_match.group(1)

                    # STAR annotation is a strong signal for PGx confidence
                    star_match = re.search(r'(?:STAR|STAR_ALLELE)=([^;]+)', info)
                    has_star_annotation = bool(star_match)

                    # RSID annotation presence in VCF row
                    has_rsid_annotation = bool(rsid and rsid != ".")

                    # Variant quality metrics
                    quality_score = None
                    if qual not in [".", ""]:
                        try:
                            quality_score = float(qual)
                        except Exception:
                            quality_score = None

                    info_dp = None
                    info_dp_match = re.search(r'(?:^|;)DP=(\d+)(?:;|$)', info)
                    if info_dp_match:
                        try:
                            info_dp = int(info_dp_match.group(1))
                        except Exception:
                            info_dp = None

                    read_depth = sample_dp if sample_dp is not None else info_dp
                    
                    detected_variants.append({
                        "rsid": rsid,
                        "gene": gene,
                        "allele": allele,
                        "function": function,
                        "cpic_level": variant_info["cpic_level"],
                        "genotype": genotype,
                        "chromosome": chrom,
                        "position": pos,
                        "ref": ref,
                        "alt": alt,
                        "quality": qual,
                        "quality_score": quality_score,
                        "read_depth": read_depth,
                        "filter": filt,
                        "info": info,
                        "has_gene_annotation": has_gene_annotation,
                        "has_star_annotation": has_star_annotation,
                        "has_rsid_annotation": has_rsid_annotation
                    })
        
        return detected_variants
        
    except Exception as e:
        print(f"VCF Parser Error: {e}")
        return []

def get_variants_by_gene(variants: List[Dict], gene: str) -> List[Dict]:
    """Filter variants by gene"""
    return [v for v in variants if v["gene"] == gene]

def get_diplotype(variants: List[Dict], gene: str) -> str:
    """
    Determine diplotype for a gene based on variants.
    Fixed version - correctly handles homozygous variants.
    """
    gene_variants = get_variants_by_gene(variants, gene)
    
    if not gene_variants:
        return "*1/*1"  # Default wild type
    
    # Collect all alleles
    alleles = []
    for v in gene_variants:
        if v["genotype"] in ["1/1", "1|1"]:
            # Homozygous variant - two copies of the variant allele
            alleles.append(v["allele"])
            alleles.append(v["allele"])
        elif v["genotype"] in ["0/1", "1/0", "0|1", "1|0"]:
            # Heterozygous - one wild type, one variant
            alleles.append("*1")
            alleles.append(v["allele"])
        elif v["genotype"] in ["0/0", "0|0"]:
            # Homozygous reference - two wild type copies
            alleles.append("*1")
            alleles.append("*1")
    
    # If we have alleles, return the first two (simplified for hackathon)
    if len(alleles) >= 2:
        # Sort to ensure consistent representation (*1/*2 not *2/*1)
        sorted_alleles = sorted(alleles[:2], key=lambda x: (x == "*1", x))
        return f"{sorted_alleles[0]}/{sorted_alleles[1]}"
    
    return "*1/*1"

def get_phenotype(gene: str, diplotype: str) -> str:
    """
    Determine phenotype based on gene and diplotype.
    Enhanced version with better pattern matching.
    """
    # CYP2D6 phenotype determination
    if gene == "CYP2D6":
        if diplotype in ["*4/*4", "*3/*3", "*5/*5", "*6/*6"]:
            return "PM"
        elif diplotype in ["*1/*4", "*1/*3", "*1/*5", "*1/*6", "*2/*4", "*4/*41"]:
            return "IM"
        elif diplotype in ["*1/*1", "*1/*2", "*2/*2"]:
            return "NM"
        elif diplotype in ["*1/*1xN", "*2/*2xN", "*1/*2xN"]:
            return "UM"
    
    # CYP2C19 phenotype determination
    elif gene == "CYP2C19":
        if diplotype in ["*2/*2", "*3/*3", "*2/*3"]:
            return "PM"
        elif diplotype in ["*1/*2", "*1/*3"]:
            return "IM"
        elif diplotype in ["*1/*1"]:
            return "NM"
        elif diplotype in ["*1/*17", "*17/*17"]:
            return "RM"
    
    # CYP2C9 phenotype determination
    elif gene == "CYP2C9":
        if diplotype in ["*3/*3", "*2/*3"]:
            return "PM"
        elif diplotype in ["*1/*2", "*1/*3", "*2/*2"]:
            return "IM"
        elif diplotype in ["*1/*1"]:
            return "NM"
    
    # SLCO1B1 phenotype (different naming)
    elif gene == "SLCO1B1":
        if "*5/*5" in diplotype:
            return "Poor function"
        elif "*1/*5" in diplotype or "*5/*1b" in diplotype:
            return "Intermediate function"
        else:
            return "Normal function"
    
    # TPMT phenotype
    elif gene == "TPMT":
        if "*2/*2" in diplotype or "*3A/*3A" in diplotype or "*3C/*3C" in diplotype:
            return "Poor metabolizer"
        elif "*1/*2" in diplotype or "*1/*3A" in diplotype or "*1/*3C" in diplotype:
            return "Intermediate metabolizer"
        else:
            return "Normal metabolizer"
    
    # DPYD phenotype
    elif gene == "DPYD":
        if "*2A/*2A" in diplotype or "*13/*13" in diplotype:
            return "Poor metabolizer"
        elif "*1/*2A" in diplotype or "*1/*13" in diplotype:
            return "Intermediate metabolizer"
        else:
            return "Normal metabolizer"
    
    return "Unknown"
