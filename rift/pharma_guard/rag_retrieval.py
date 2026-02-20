"""
RAG Retrieval Module for PharmaGuard
Fetches CPIC guidelines from SQLite database for LLM grounding
"""

import sqlite3
import os
from typing import Dict, Optional, Any, List
from database import DB_PATH

class GuidelineRetriever:
    """Retrieves CPIC guidelines from database for RAG"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        
    def _connect(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def normalize_phenotype(self, phenotype: str) -> Optional[str]:
        """
        Convert various phenotype strings to standard codes
        PM, IM, NM, RM, UM
        """
        phenotype_map = {
            # Standard codes
            "PM": "PM", "IM": "IM", "NM": "NM", "RM": "RM", "UM": "UM",
            
            # Full names
            "Poor Metabolizer": "PM",
            "Intermediate Metabolizer": "IM", 
            "Normal Metabolizer": "NM",
            "Rapid Metabolizer": "RM",
            "Ultrarapid Metabolizer": "UM",
            
            # Function variants
            "Poor function": "PM",
            "Intermediate function": "IM",
            "Normal function": "NM",
            
            # Lowercase variants
            "poor metabolizer": "PM",
            "intermediate metabolizer": "IM",
            "normal metabolizer": "NM",
            "rapid metabolizer": "RM",
            "ultrarapid metabolizer": "UM",
            "poor function": "PM",
            "intermediate function": "IM",
            "normal function": "NM"
        }
        
        return phenotype_map.get(phenotype)
    
    def get_guideline(self, drug: str, phenotype: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve guideline for specific drug and phenotype
        
        Args:
            drug: Drug name (e.g., "CODEINE")
            phenotype: Phenotype string (e.g., "PM", "Poor Metabolizer")
            
        Returns:
            Dictionary with guideline data or None if not found
        """
        conn = self._connect()
        cursor = conn.cursor()
        
        # Normalize phenotype
        norm_pheno = self.normalize_phenotype(phenotype)
        if not norm_pheno:
            print(f"⚠️ Unknown phenotype: {phenotype}")
            conn.close()
            return None
        
        # Query database
        cursor.execute('''
            SELECT 
                p.phenotype_code,
                p.phenotype_name,
                p.summary,
                p.mechanism,
                p.recommendation,
                p.source,
                p.guideline_url,
                p.confidence_score,
                d.name as drug_name,
                d.gene
            FROM phenotypes p
            JOIN drugs d ON d.id = p.drug_id
            WHERE d.name = ? AND p.phenotype_code = ?
        ''', (drug.upper(), norm_pheno))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_drug_info(self, drug: str) -> Optional[Dict[str, Any]]:
        """Get basic drug information"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, gene
            FROM drugs
            WHERE name = ?
        ''', (drug.upper(),))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_phenotypes_for_drug(self, drug: str) -> List[Dict]:
        """Get all available phenotypes for a drug"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT phenotype_code, phenotype_name
            FROM phenotypes p
            JOIN drugs d ON d.id = p.drug_id
            WHERE d.name = ?
            ORDER BY phenotype_code
        ''', (drug.upper(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def format_for_llm(self, guideline: Dict[str, Any]) -> str:
        """Format guideline for inclusion in LLM prompt"""
        if not guideline:
            return ""
        
        return f"""
CPIC GUIDELINE:
Drug: {guideline['drug_name']}
Gene: {guideline['gene']}
Phenotype: {guideline['phenotype_name']} ({guideline['phenotype_code']})

Summary: {guideline['summary']}

Mechanism: {guideline['mechanism']}

Recommendation: {guideline['recommendation']}

Source: {guideline['source']}
URL: {guideline['guideline_url']}
Confidence: {guideline['confidence_score']}
"""

# Test function
def test_retriever():
    """Test the retriever with some queries"""
    retriever = GuidelineRetriever()
    
    test_cases = [
        ("CODEINE", "PM"),
        ("CODEINE", "Poor Metabolizer"),
        ("CLOPIDOGREL", "IM"),
        ("WARFARIN", "NM"),
        ("SIMVASTATIN", "Poor function"),
        ("AZATHIOPRINE", "Normal Metabolizer"),
        ("FLUOXETINE", "PM"),
    ]
    
    print("🔍 Testing Guideline Retriever\n")
    
    for drug, pheno in test_cases:
        print(f"Query: {drug} - {pheno}")
        guideline = retriever.get_guideline(drug, pheno)
        
        if guideline:
            print(f"✅ Found: {guideline['phenotype_name']}")
            print(f"   Summary: {guideline['summary'][:80]}...")
            print(f"   Source: {guideline['source']}")
        else:
            print(f"❌ Not found")
        print()

if __name__ == "__main__":
    test_retriever()