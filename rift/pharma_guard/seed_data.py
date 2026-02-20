"""
Seed the database with CPIC guidelines for all supported drugs
Run this once to populate the database
"""

import sqlite3
import os
from database import DB_PATH

# Complete guideline data for all drugs
GUIDELINE_DATA = {
    "CODEINE": {
        "gene": "CYP2D6",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "CYP2D6 poor metabolizers have significantly reduced conversion of codeine to morphine, leading to inadequate analgesia.",
                "mechanism": "Codeine is a prodrug that requires activation by CYP2D6 to morphine. PMs lack this activity, resulting in 80-90% lower morphine concentrations.",
                "recommendation": "AVOID codeine. Use alternative analgesics not dependent on CYP2D6 (morphine, hydromorphone, oxycodone).",
                "source": "CPIC Guideline for Codeine and CYP2D6 (2023)",
                "url": "https://cpicpgx.org/guidelines/codeine-and-cyp2d6/"
            },
            "IM": {
                "name": "Intermediate Metabolizer",
                "summary": "CYP2D6 intermediate metabolizers have reduced conversion of codeine to morphine, potentially leading to suboptimal analgesia.",
                "mechanism": "IMs have one functional allele, resulting in approximately 30-50% of normal enzyme activity and proportionally reduced morphine formation.",
                "recommendation": "Consider alternative analgesics or monitor closely for efficacy. If used, standard dosing may be inadequate.",
                "source": "CPIC Guideline for Codeine and CYP2D6 (2023)",
                "url": "https://cpicpgx.org/guidelines/codeine-and-cyp2d6/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "CYP2D6 normal metabolizers have expected conversion of codeine to morphine with standard dosing.",
                "mechanism": "NMs have two functional alleles, providing normal enzyme activity and predictable morphine formation.",
                "recommendation": "Use codeine at standard doses. Monitor for efficacy and side effects.",
                "source": "CPIC Guideline for Codeine and CYP2D6 (2023)",
                "url": "https://cpicpgx.org/guidelines/codeine-and-cyp2d6/"
            },
            "UM": {
                "name": "Ultrarapid Metabolizer",
                "summary": "CYP2D6 ultrarapid metabolizers have dangerously increased conversion of codeine to morphine, risking life-threatening toxicity.",
                "mechanism": "UMs have multiple functional alleles or gene duplications, leading to 2-4x higher morphine formation and risk of respiratory depression.",
                "recommendation": "AVOID codeine. Life-threatening toxicity risk. Use alternative analgesics.",
                "source": "CPIC Guideline for Codeine and CYP2D6 (2023)",
                "url": "https://cpicpgx.org/guidelines/codeine-and-cyp2d6/"
            }
        }
    },
    
    "CLOPIDOGREL": {
        "gene": "CYP2C19",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "CYP2C19 poor metabolizers have significantly reduced activation of clopidogrel, leading to higher risk of cardiovascular events.",
                "mechanism": "Clopidogrel requires CYP2C19-mediated activation. PMs have two loss-of-function alleles, reducing active metabolite formation by 60-70%.",
                "recommendation": "AVOID clopidogrel. Use alternative antiplatelet therapy (prasugrel, ticagrelor).",
                "source": "CPIC Guideline for Clopidogrel and CYP2C19 (2022)",
                "url": "https://cpicpgx.org/guidelines/clopidogrel-and-cyp2c19/"
            },
            "IM": {
                "name": "Intermediate Metabolizer",
                "summary": "CYP2C19 intermediate metabolizers have reduced clopidogrel activation, potentially increasing cardiovascular event risk.",
                "mechanism": "IMs have one loss-of-function allele, reducing active metabolite formation by 30-50% compared to NMs.",
                "recommendation": "Consider alternative antiplatelet therapy or use higher doses with monitoring.",
                "source": "CPIC Guideline for Clopidogrel and CYP2C19 (2022)",
                "url": "https://cpicpgx.org/guidelines/clopidogrel-and-cyp2c19/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "CYP2C19 normal metabolizers have expected clopidogrel activation with standard dosing.",
                "mechanism": "NMs have two functional alleles, providing normal enzyme activity and therapeutic active metabolite levels.",
                "recommendation": "Use clopidogrel at standard dose (75mg/day).",
                "source": "CPIC Guideline for Clopidogrel and CYP2C19 (2022)",
                "url": "https://cpicpgx.org/guidelines/clopidogrel-and-cyp2c19/"
            },
            "RM": {
                "name": "Rapid Metabolizer",
                "summary": "CYP2C19 rapid metabolizers have increased clopidogrel activation, potentially increasing bleeding risk.",
                "mechanism": "RMs have a gain-of-function allele (*17), resulting in 20-40% higher active metabolite levels.",
                "recommendation": "Standard dosing is appropriate, but monitor for bleeding.",
                "source": "CPIC Guideline for Clopidogrel and CYP2C19 (2022)",
                "url": "https://cpicpgx.org/guidelines/clopidogrel-and-cyp2c19/"
            }
        }
    },
    
    "WARFARIN": {
        "gene": "CYP2C9",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "CYP2C9 poor metabolizers have significantly reduced warfarin clearance, requiring substantial dose reduction.",
                "mechanism": "Warfarin is metabolized by CYP2C9. PMs have two reduced-function alleles (*2, *3), decreasing clearance by 70-90%.",
                "recommendation": "SIGNIFICANTLY REDUCE dose. Start at 1-2mg/day. Use pharmacogenetic dosing algorithms.",
                "source": "CPIC Guideline for Warfarin and CYP2C9/VKORC1 (2021)",
                "url": "https://cpicpgx.org/guidelines/warfarin-and-cyp2c9-vkorc1/"
            },
            "IM": {
                "name": "Intermediate Metabolizer",
                "summary": "CYP2C9 intermediate metabolizers have reduced warfarin clearance, requiring moderate dose reduction.",
                "mechanism": "IMs have one reduced-function allele, decreasing clearance by 30-50%.",
                "recommendation": "REDUCE dose by 20-30%. Start at 3-4mg/day. Monitor INR closely.",
                "source": "CPIC Guideline for Warfarin and CYP2C9/VKORC1 (2021)",
                "url": "https://cpicpgx.org/guidelines/warfarin-and-cyp2c9-vkorc1/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "CYP2C9 normal metabolizers have expected warfarin clearance with standard dosing.",
                "mechanism": "NMs have two functional alleles, providing normal enzyme activity.",
                "recommendation": "Start with standard dosing (5mg/day). Monitor INR and adjust based on response.",
                "source": "CPIC Guideline for Warfarin and CYP2C9/VKORC1 (2021)",
                "url": "https://cpicpgx.org/guidelines/warfarin-and-cyp2c9-vkorc1/"
            }
        }
    },
    
    "SIMVASTATIN": {
        "gene": "SLCO1B1",
        "phenotypes": {
            "PM": {
                "name": "Poor Function",
                "summary": "SLCO1B1 poor function significantly increases simvastatin exposure and myopathy risk.",
                "mechanism": "SLCO1B1 transports statins into hepatocytes. Poor function variants (e.g., *5/*5) reduce hepatic uptake by 70-90%.",
                "recommendation": "SIGNIFICANTLY REDUCE dose or consider alternative statin. Max dose 20mg/day.",
                "source": "CPIC Guideline for Simvastatin and SLCO1B1 (2022)",
                "url": "https://cpicpgx.org/guidelines/simvastatin-and-slco1b1/"
            },
            "IM": {
                "name": "Intermediate Function",
                "summary": "SLCO1B1 intermediate function moderately increases simvastatin exposure.",
                "mechanism": "Heterozygous variants (e.g., *1/*5) reduce hepatic uptake by 30-50%.",
                "recommendation": "REDUCE dose or consider alternative statin. Max dose 40mg/day.",
                "source": "CPIC Guideline for Simvastatin and SLCO1B1 (2022)",
                "url": "https://cpicpgx.org/guidelines/simvastatin-and-slco1b1/"
            },
            "NM": {
                "name": "Normal Function",
                "summary": "SLCO1B1 normal function provides expected simvastatin disposition.",
                "mechanism": "Normal SLCO1B1 activity ensures adequate hepatic uptake and clearance.",
                "recommendation": "Use standard doses (up to 40mg/day).",
                "source": "CPIC Guideline for Simvastatin and SLCO1B1 (2022)",
                "url": "https://cpicpgx.org/guidelines/simvastatin-and-slco1b1/"
            }
        }
    },
    
    "AZATHIOPRINE": {
        "gene": "TPMT",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "TPMT poor metabolizers have life-threatening myelosuppression risk with azathioprine.",
                "mechanism": "TPMT inactivates azathioprine metabolites. PMs have no TPMT activity, leading to 10-15x higher thioguanine nucleotide accumulation.",
                "recommendation": "AVOID azathioprine. Use alternative immunosuppressants or reduce dose by 90% with extreme caution.",
                "source": "CPIC Guideline for Azathioprine and TPMT (2021)",
                "url": "https://cpicpgx.org/guidelines/azathioprine-and-tpmt/"
            },
            "IM": {
                "name": "Intermediate Metabolizer",
                "summary": "TPMT intermediate metabolizers have increased myelosuppression risk requiring dose reduction.",
                "mechanism": "Heterozygous variants reduce TPMT activity by 50-70%, moderately increasing thioguanine nucleotide levels.",
                "recommendation": "REDUCE dose by 30-70%. Start at 30-50% of standard dose.",
                "source": "CPIC Guideline for Azathioprine and TPMT (2021)",
                "url": "https://cpicpgx.org/guidelines/azathioprine-and-tpmt/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "TPMT normal metabolizers have expected azathioprine metabolism with standard dosing.",
                "mechanism": "Normal TPMT activity ensures adequate inactivation of metabolites.",
                "recommendation": "Use standard doses (2-3 mg/kg/day).",
                "source": "CPIC Guideline for Azathioprine and TPMT (2021)",
                "url": "https://cpicpgx.org/guidelines/azathioprine-and-tpmt/"
            }
        }
    },
    
    "FLUOROURACIL": {
        "gene": "DPYD",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "DPYD poor metabolizers have life-threatening toxicity risk with fluorouracil.",
                "mechanism": "DPYD inactivates >80% of fluorouracil. PMs have no DPYD activity, leading to severe, prolonged drug exposure.",
                "recommendation": "AVOID fluorouracil. Use alternative chemotherapy.",
                "source": "CPIC Guideline for Fluorouracil and DPYD (2022)",
                "url": "https://cpicpgx.org/guidelines/fluorouracil-and-dpyd/"
            },
            "IM": {
                "name": "Intermediate Metabolizer",
                "summary": "DPYD intermediate metabolizers have increased toxicity risk requiring dose reduction.",
                "mechanism": "Heterozygous variants reduce DPYD activity by 30-50%, moderately increasing drug exposure.",
                "recommendation": "REDUCE dose by 50%. Monitor closely for toxicity.",
                "source": "CPIC Guideline for Fluorouracil and DPYD (2022)",
                "url": "https://cpicpgx.org/guidelines/fluorouracil-and-dpyd/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "DPYD normal metabolizers have expected fluorouracil clearance.",
                "mechanism": "Normal DPYD activity ensures adequate drug inactivation.",
                "recommendation": "Use standard doses.",
                "source": "CPIC Guideline for Fluorouracil and DPYD (2022)",
                "url": "https://cpicpgx.org/guidelines/fluorouracil-and-dpyd/"
            }
        }
    },
    
    "FLUOXETINE": {
        "gene": "CYP2D6",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "CYP2D6 poor metabolizers have significantly higher fluoxetine concentrations, increasing side effect risk.",
                "mechanism": "Fluoxetine is metabolized by CYP2D6. PMs have 2-4x higher drug levels.",
                "recommendation": "REDUCE dose by 50%. Start at 10mg/day.",
                "source": "CPIC Guideline for SSRIs and CYP2D6 (2022)",
                "url": "https://cpicpgx.org/guidelines/ssri-and-cyp2d6/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "CYP2D6 normal metabolizers have expected fluoxetine metabolism.",
                "mechanism": "Normal CYP2D6 activity provides standard drug clearance.",
                "recommendation": "Use standard doses (20mg/day).",
                "source": "CPIC Guideline for SSRIs and CYP2D6 (2022)",
                "url": "https://cpicpgx.org/guidelines/ssri-and-cyp2d6/"
            }
        }
    },
    
    "PAROXETINE": {
        "gene": "CYP2D6",
        "phenotypes": {
            "PM": {
                "name": "Poor Metabolizer",
                "summary": "CYP2D6 poor metabolizers have significantly higher paroxetine concentrations, increasing side effect risk.",
                "mechanism": "Paroxetine is extensively metabolized by CYP2D6. PMs have 3-5x higher drug levels.",
                "recommendation": "REDUCE dose by 50%. Start at 10mg/day.",
                "source": "CPIC Guideline for SSRIs and CYP2D6 (2022)",
                "url": "https://cpicpgx.org/guidelines/ssri-and-cyp2d6/"
            },
            "NM": {
                "name": "Normal Metabolizer",
                "summary": "CYP2D6 normal metabolizers have expected paroxetine metabolism.",
                "mechanism": "Normal CYP2D6 activity provides standard drug clearance.",
                "recommendation": "Use standard doses (20mg/day).",
                "source": "CPIC Guideline for SSRIs and CYP2D6 (2022)",
                "url": "https://cpicpgx.org/guidelines/ssri-and-cyp2d6/"
            }
        }
    }
}

def seed_database():
    """Populate database with guideline data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for drug_name, drug_data in GUIDELINE_DATA.items():
        # Insert drug
        cursor.execute(
            "INSERT OR IGNORE INTO drugs (name, gene) VALUES (?, ?)",
            (drug_name, drug_data["gene"])
        )
        
        # Get drug_id
        cursor.execute("SELECT id FROM drugs WHERE name = ?", (drug_name,))
        drug_id = cursor.fetchone()[0]
        
        # Insert phenotypes
        for pheno_code, pheno_data in drug_data["phenotypes"].items():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO phenotypes 
                    (drug_id, phenotype_code, phenotype_name, summary, mechanism, 
                     recommendation, source, guideline_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    drug_id, pheno_code, pheno_data["name"],
                    pheno_data["summary"], pheno_data["mechanism"],
                    pheno_data["recommendation"], pheno_data["source"],
                    pheno_data["url"]
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting {drug_name} {pheno_code}: {e}")
                skipped += 1
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database seeded successfully!")
    print(f"   📊 Inserted: {inserted} phenotype guidelines")
    print(f"   ⏭️  Skipped: {skipped}")
    print("\n   Drugs added:")
    for drug in GUIDELINE_DATA.keys():
        print(f"   • {drug} ({GUIDELINE_DATA[drug]['gene']})")

if __name__ == "__main__":
    seed_database()