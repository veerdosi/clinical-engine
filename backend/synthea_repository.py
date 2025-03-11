# backend/synthea_repository.py
import json
import sqlite3
import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SyntheaRepository:
    def __init__(self, db_path="synthea_patients.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database structure"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create main patient templates table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_templates (
                id TEXT PRIMARY KEY,
                raw_data JSON,
                primary_diagnosis TEXT,
                specialty TEXT,
                difficulty TEXT,
                age INTEGER,
                gender TEXT,
                presenting_complaint TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create index for faster retrieval
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_specialty ON patient_templates(specialty)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_difficulty ON patient_templates(difficulty)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_diagnosis ON patient_templates(primary_diagnosis)')
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully initialized Synthea repository at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing Synthea repository: {str(e)}")
            raise
    
    def import_patient(self, patient_data: Dict[str, Any], specialty: str, difficulty: str) -> str:
        """Import a single patient record with specialty and difficulty metadata"""
        try:
            # Extract key information for indexing
            patient_id = patient_data.get('id', f"patient_{len(self.get_all_patient_ids()) + 1}")
            
            # Extract primary diagnosis (simplistic approach - you'd want a more robust method)
            diagnoses = []
            for entry in patient_data.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Condition':
                    diagnoses.append(resource.get('code', {}).get('text', ''))
            
            primary_diagnosis = diagnoses[0] if diagnoses else "Unknown"
            
            # Extract age and gender
            gender = patient_data.get('gender', 'unknown')
            birth_date = patient_data.get('birthDate', '')
            # Simplified age calculation - you'd want to do this properly
            age = 2025 - int(birth_date.split('-')[0]) if birth_date else 0
            
            # Generate a presenting complaint (simplified)
            presenting_complaint = f"Patient with {primary_diagnosis}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO patient_templates 
            (id, raw_data, primary_diagnosis, specialty, difficulty, age, gender, presenting_complaint)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id,
                json.dumps(patient_data),
                primary_diagnosis,
                specialty,
                difficulty,
                age,
                gender,
                presenting_complaint
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Imported patient {patient_id} with diagnosis {primary_diagnosis}")
            return patient_id
            
        except Exception as e:
            logger.error(f"Error importing patient data: {str(e)}")
            raise
    
    def find_matching_patient(self, 
                             specialty: Optional[str] = None, 
                             difficulty: Optional[str] = None, 
                             gender: Optional[str] = None,
                             min_age: Optional[int] = None,
                             max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Find a patient matching the given criteria"""
        try:
            query_parts = ["SELECT id, raw_data, primary_diagnosis, specialty, difficulty, age, gender, presenting_complaint FROM patient_templates WHERE 1=1"]
            params = []
            
            if specialty:
                query_parts.append("AND specialty = ?")
                params.append(specialty)
                
            if difficulty:
                query_parts.append("AND difficulty = ?")
                params.append(difficulty)
                
            if gender:
                query_parts.append("AND gender = ?")
                params.append(gender)
                
            if min_age is not None:
                query_parts.append("AND age >= ?")
                params.append(min_age)
                
            if max_age is not None:
                query_parts.append("AND age <= ?")
                params.append(max_age)
            
            # Add randomization to get different patients
            query_parts.append("ORDER BY RANDOM() LIMIT 1")
            
            query = " ".join(query_parts)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if not row:
                return None
                
            patient = dict(row)
            patient['raw_data'] = json.loads(patient['raw_data'])
            
            conn.close()
            return patient
            
        except Exception as e:
            logger.error(f"Error finding matching patient: {str(e)}")
            return None
    
    def get_all_patient_ids(self) -> List[str]:
        """Get list of all patient IDs in the repository"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM patient_templates")
            ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return ids
            
        except Exception as e:
            logger.error(f"Error retrieving patient IDs: {str(e)}")
            return []