"""
PharmaGuard SQLite Database Manager
Stores CPIC guidelines for all drugs - Scalable, queryable, production-ready
"""

import sqlite3
import os
from typing import Dict, List, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), 'pharmaguard.db')

def init_database():
    """Initialize the database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create drugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            gene TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create phenotypes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phenotypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_id INTEGER NOT NULL,
            phenotype_code TEXT NOT NULL,  -- PM, IM, NM, RM, UM
            phenotype_name TEXT NOT NULL,   -- Poor Metabolizer, etc.
            summary TEXT NOT NULL,
            mechanism TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            source TEXT NOT NULL,
            guideline_url TEXT NOT NULL,
            confidence_score REAL DEFAULT 0.95,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (drug_id) REFERENCES drugs (id),
            UNIQUE(drug_id, phenotype_code)
        )
    ''')
    
    # Create index for fast lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_drug_phenotype 
        ON phenotypes(drug_id, phenotype_code)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")
    print(f"📁 Database location: {DB_PATH}")

# Run this once to create the database
if __name__ == "__main__":
    init_database()