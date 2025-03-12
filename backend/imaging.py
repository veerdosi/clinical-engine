import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import Client

logger = logging.getLogger(__name__)

class ImagingSystem:
    """
    System for generating radiology reports based on imaging studies ordered.
    Provides detailed, realistic text reports without generating actual images.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
        self.results_cache = {}  # Cache to store generated reports
        
        # Define common imaging modalities and their properties
        self.imaging_modalities = {
            "CXR": {
                "name": "Chest X-ray",
                "description": "Posteroanterior and lateral chest radiograph",
                "radiation_dose": "Low",
                "duration": "Less than 1 minute",
                "preparation": "None required"
            },
            "CT Chest": {
                "name": "CT Chest",
                "description": "Computed tomography of the chest with IV contrast",
                "radiation_dose": "Moderate to high",
                "duration": "5-10 minutes",
                "preparation": "NPO for 4 hours prior if contrast used"
            },
            "CT Abdomen/Pelvis": {
                "name": "CT Abdomen/Pelvis",
                "description": "Computed tomography of the abdomen and pelvis with IV and oral contrast",
                "radiation_dose": "Moderate to high",
                "duration": "10-15 minutes",
                "preparation": "NPO for 4 hours prior, oral contrast 1-2 hours before scan"
            },
            "MRI Brain": {
                "name": "MRI Brain",
                "description": "Magnetic resonance imaging of the brain with and without contrast",
                "radiation_dose": "None",
                "duration": "30-45 minutes",
                "preparation": "Remove all metal objects, inform of implants"
            },
            "Ultrasound Abdomen": {
                "name": "Ultrasound Abdomen",
                "description": "Abdominal ultrasonography",
                "radiation_dose": "None",
                "duration": "15-30 minutes",
                "preparation": "NPO for 6 hours prior"
            },
            "ECG": {
                "name": "Electrocardiogram",
                "description": "12-lead electrocardiogram",
                "radiation_dose": "None",
                "duration": "Less than 5 minutes",
                "preparation": "None required"
            },
            "Echocardiogram": {
                "name": "Echocardiogram",
                "description": "Transthoracic echocardiogram",
                "radiation_dose": "None",
                "duration": "30-45 minutes",
                "preparation": "None required"
            },
            "X-ray": {
                "name": "Plain Radiograph",
                "description": "Plain film radiography",
                "radiation_dose": "Low",
                "duration": "Less than 5 minutes",
                "preparation": "None required"
            }
        }
    
    def _get_cache_key(self, case_id: str, modality: str) -> str:
        """
        Generate a unique cache key for a case and imaging modality.
        """
        return f"{case_id}:{modality}"
    
    def generate_report(self, case: Dict[str, Any], modality: str) -> Dict[str, Any]:
        """
        Generate a detailed radiology report based on the case and imaging modality.
        
        Args:
            case: The patient case information
            modality: The requested imaging modality (e.g., "CXR", "CT Chest")
            
        Returns:
            Dict containing the radiology report and metadata
        """
        # Check cache first
        cache_key = self._get_cache_key(case.get("id", "unknown"), modality)
        if cache_key in self.results_cache:
            logger.info(f"Using cached imaging report for {cache_key}")
            cached_result = self.results_cache[cache_key].copy()
            
            # Update timestamp for fresh appearance
            cached_result["timestamp"] = datetime.now().isoformat()
            return cached_result
        
        # Get modality information
        modality_info = self.imaging_modalities.get(modality, {
            "name": modality,
            "description": f"{modality} imaging study",
            "radiation_dose": "Unknown",
            "duration": "Unknown",
            "preparation": "Unknown"
        })
        
        try:
            # Generate results using LLM
            system_prompt = f"""You are an experienced radiologist generating a detailed radiology report.

Patient Information:
- Name: {case.get('name', 'Unknown')}
- Age: {case.get('age', 'Unknown')}
- Gender: {case.get('gender', 'Unknown')}
- Clinical History: {case.get('presenting_complaint', 'Unknown')}

Imaging Study: {modality_info['name']} ({modality_info['description']})

Generate a comprehensive radiology report with these sections:
1. EXAMINATION: Brief description of the procedure performed
2. CLINICAL INDICATION: Why the study was ordered
3. TECHNIQUE: Technical details of how the study was performed
4. FINDINGS: Detailed observations organized by anatomical regions or systems
5. IMPRESSION: Summary interpretation with differential diagnosis (3-4 items in order of likelihood)

The patient has a diagnosis of: {case.get('diagnosis', 'Unknown')}

The findings should be consistent with this diagnosis, but include some incidental findings as well.
Use proper radiology terminology and be specific with anatomical descriptions.
Format the report professionally as would appear in a medical record.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a radiology report for: {modality}"}
                ],
                temperature=0.4
            )
            
            # Extract the report text
            report_text = response.choices[0].message.content.strip()
            
            # Structure the report information
            report_info = {
                "case_id": case.get("id", "unknown"),
                "patient_name": case.get("name", "Unknown"),
                "patient_id": f"MRN-{case.get('id', '000000')[-6:]}",
                "modality": modality,
                "modality_details": modality_info,
                "ordering_provider": "Medical Student",
                "timestamp": datetime.now().isoformat(),
                "report_text": report_text,
                "report_id": f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "radiologist": "AI Generated Report"
            }
            
            # Parse sections for structured access
            report_info["structured_sections"] = self._parse_report_sections(report_text)
            
            # Cache the report
            self.results_cache[cache_key] = report_info
            
            return report_info
            
        except Exception as e:
            logger.error(f"Error generating imaging report: {str(e)}")
            
            # Generate fallback report
            fallback_report = self._generate_fallback_report(case, modality, modality_info)
            
            return fallback_report
    
    def _parse_report_sections(self, report_text: str) -> Dict[str, str]:
        """
        Parse the sections from the report text.
        
        Args:
            report_text: The full report text
            
        Returns:
            Dict with each section's content
        """
        sections = {
            "EXAMINATION": "",
            "CLINICAL INDICATION": "",
            "TECHNIQUE": "",
            "FINDINGS": "",
            "IMPRESSION": ""
        }
        
        current_section = None
        section_content = []
        
        # Split text into lines and process
        lines = report_text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Check if this is a section header
            upper_line = line.upper()
            found_section = False
            
            for section in sections.keys():
                if section in upper_line or upper_line.startswith(section.split()[0]):
                    # If we were collecting content for a previous section, save it
                    if current_section:
                        sections[current_section] = '\n'.join(section_content).strip()
                    
                    # Start new section
                    current_section = section
                    section_content = []
                    found_section = True
                    break
            
            if not found_section and current_section:
                # Continue collecting content for the current section
                section_content.append(line)
        
        # Save the last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    def _generate_fallback_report(self, case: Dict[str, Any], modality: str, 
                                 modality_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a basic fallback report when LLM generation fails.
        
        Args:
            case: The patient case
            modality: Imaging modality requested
            modality_info: Information about the modality
            
        Returns:
            Dict containing a basic report
        """
        # Generic normal report template
        report_text = f"""EXAMINATION: {modality_info['name']}

CLINICAL INDICATION: {case.get('presenting_complaint', 'Evaluation')}

TECHNIQUE: {modality_info['description']}

FINDINGS:
No acute abnormalities identified.
Normal anatomical structures visualized.
No evidence of fracture, dislocation, or soft tissue abnormality.
No suspicious masses or lesions.

IMPRESSION:
1. Normal {modality_info['name']} study.
2. Clinical correlation recommended if symptoms persist."""
        
        # Structure the report information
        report_info = {
            "case_id": case.get("id", "unknown"),
            "patient_name": case.get("name", "Unknown"),
            "patient_id": f"MRN-{case.get('id', '000000')[-6:]}",
            "modality": modality,
            "modality_details": modality_info,
            "ordering_provider": "Medical Student",
            "timestamp": datetime.now().isoformat(),
            "report_text": report_text,
            "report_id": f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "radiologist": "AI Generated Report (Fallback)",
            "structured_sections": self._parse_report_sections(report_text)
        }
        
        return report_info
    
    def generate_markdown_report(self, report_info: Dict[str, Any]) -> str:
        """
        Generate a formatted markdown report from the structured data.
        
        Args:
            report_info: The structured report information
            
        Returns:
            Markdown formatted imaging report
        """
        # Extract data from report_info
        modality = report_info.get("modality", "Unknown")
        modality_details = report_info.get("modality_details", {})
        timestamp = report_info.get("timestamp", "Unknown")
        radiologist = report_info.get("radiologist", "Unknown")
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_timestamp = dt.strftime("%B %d, %Y %I:%M %p")
        except:
            formatted_timestamp = timestamp
            
        # Structured sections or full text
        if "structured_sections" in report_info:
            sections = report_info["structured_sections"]
            
            # Create the markdown report
            md_report = f"# {modality} Report\n\n"
            md_report += f"**Date/Time:** {formatted_timestamp}\n"
            md_report += f"**Radiologist:** {radiologist}\n\n"
            
            # Add procedure information
            md_report += "## Procedure Information\n\n"
            md_report += f"**Procedure:** {modality_details.get('name', modality)}\n"
            md_report += f"**Description:** {modality_details.get('description', 'Not specified')}\n"
            md_report += f"**Radiation Dose:** {modality_details.get('radiation_dose', 'Not specified')}\n"
            md_report += f"**Procedure Duration:** {modality_details.get('duration', 'Not specified')}\n\n"
            
            # Add each section
            for section, content in sections.items():
                if content:
                    md_report += f"## {section}\n\n{content}\n\n"
        else:
            # Use the full report text
            md_report = f"# {modality} Report\n\n"
            md_report += f"**Date/Time:** {formatted_timestamp}\n"
            md_report += f"**Radiologist:** {radiologist}\n\n"
            md_report += report_info.get("report_text", "No report available.")
            
        return md_report

    def generate_imaging_prompt(case: Dict[str, Any], modality: str, config) -> Dict[str, Any]:
        """
        Generates a natural language prompt for radiology report generation.
        This is a legacy function maintained for compatibility.
        
        Args:
            case: Patient case information
            modality: Requested imaging modality
            config: Configuration object
            
        Returns:
            Dict with parameters for report generation
        """
        system_prompt = f"""You are a radiologist assistant. Create imaging reports for:
    Patient Case: {json.dumps(case)}
    Modality: {modality}

    Create a natural language description of radiological findings that would be 
    consistent with this case. Focus on what would be visible in this imaging modality
    for a patient with the given symptoms and likely diagnosis.

    Example output:
    {{
        "clinical_indication": "45yo male with chest pain",
        "findings_description": "PA chest X-ray showing left lower lobe consolidation with air bronchograms, consistent with pneumonia.",
        "diagnostic_hints": ["Pneumonia", "Pulmonary edema"]
    }}"""
        
        try:
            client = Client(api_key=config.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate standard imaging study for {modality}"}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            imaging_data = json.loads(response.choices[0].message.content)
            return imaging_data
        except Exception as e:
            logger.error(f"Error generating imaging prompt: {str(e)}")
            return {
                "clinical_indication": case.get("presenting_complaint", "Unknown"),
                "findings_description": f"Standard {modality} with no significant abnormalities.",
                "diagnostic_hints": [case.get("diagnosis", "Unknown")]
            }