import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import Client

import os
import requests
import io
from PIL import Image

logger = logging.getLogger(__name__)

class ImagingSystem:
    """
    System for generating radiology reports based on imaging studies ordered.
    Provides detailed, realistic text reports.
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
    
    def generate_image_prompt(self, case: Dict[str, Any], modality: str) -> str:
        """
        Generate a concise prompt for an image model based on the case and imaging modality.
        Limited to approximately 77 tokens to fit API requirements.
        
        Args:
            case: The patient case information
            modality: The requested imaging modality
            
        Returns:
            A string prompt for the image generation model
        """
        # Get modality information
        modality_info = self.imaging_modalities.get(modality, {
            "name": modality,
            "description": f"{modality} imaging study"
        })
        
        # Extract key clinical information
        diagnosis = case.get('diagnosis', '').lower()
        complaint = case.get('presenting_complaint', '').lower()
        
        # Map modality to appropriate image type
        modality_name = modality_info["name"]
        
        # For X-ray types, specify view
        view_spec = ""
        if modality == "CXR":
            view_spec = "PA and lateral view"
        elif "X-ray" in modality:
            # For other X-rays, determine appropriate view based on case
            body_part = modality.replace("X-ray", "").strip()
            view_spec = f"{body_part} view"
        
        # Generate a concise, focused prompt
        prompt = f"Generate {modality_name} {view_spec} showing {diagnosis if diagnosis else complaint}. Medical imaging, realistic."
        
        # Truncate if necessary to ensure token limit
        if len(prompt.split()) > 20:  # Rough approximation of 77 tokens
            prompt = " ".join(prompt.split()[:20])
        
        return prompt
    
    def call_image_api(self, prompt: str, save_path: Optional[str] = None) -> Optional[Image.Image]:
        """
        Call the remote text-to-image API with a prompt and return the generated image.
        
        Args:
            prompt: The text prompt to generate an image from
            save_path: Optional path to save the image to
            
        Returns:
            PIL Image object or None if the request failed
        """
        try:
            # Replace with your remote server IP address
            api_url = "http://127.0.0.1:5001/generate"
            
            # Prepare the request
            headers = {"Content-Type": "application/json"}
            data = {"prompt": prompt}
            
            # Send the request
            response = requests.post(api_url, json=data, headers=headers, timeout=60)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Convert the response content to an image
                image = Image.open(io.BytesIO(response.content))
                
                # Save the image if a path was provided
                if save_path:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
                    image.save(save_path)
                    print(f"Image saved to {save_path}")
                    
                return image
            else:
                print(f"API request failed with status code {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling image API: {str(e)}")
            return None