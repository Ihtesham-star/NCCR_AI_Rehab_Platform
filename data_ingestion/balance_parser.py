"""
PDF Parser for TecnoBody Balance Test Reports
Extracts balance and stability metrics from balance test PDFs
"""
import re
from typing import Dict, Optional
from datetime import datetime
import pdfplumber


class BalanceTestParser:
    """Parser for TecnoBody balance test PDF reports"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.data = {
            'patient_info': {},
            'balance_metrics': {},
            'metadata': {}
        }
    
    def parse(self) -> Dict:
        """Parse the entire PDF and extract all data"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    
                    # Extract patient information
                    self._extract_patient_info(text)
                    
                    # Extract balance metrics
                    self._extract_balance_metrics(text)
                    
                    # Extract trunk sway data
                    self._extract_trunk_sway(text)
            
            return self.data
        
        except Exception as e:
            raise Exception(f"Error parsing Balance PDF: {str(e)}")
    
    def _extract_patient_info(self, text: str):
        """Extract patient information"""
        # Extract name
        name_match = re.search(r'Name\s+([A-Z\s]+)', text)
        if name_match:
            self.data['patient_info']['name'] = name_match.group(1).strip()
        
        # Extract date of birth
        dob_match = re.search(r'Date of birth\s+(\d{1,2}/\d{1,2}/\d{4})', text)
        if dob_match:
            self.data['patient_info']['date_of_birth'] = dob_match.group(1)
        
        # Extract height
        height_match = re.search(r'Height.*?(\d+)\s*cm', text, re.IGNORECASE)
        if height_match:
            self.data['patient_info']['height_cm'] = int(height_match.group(1))
        
        # Extract weight
        weight_match = re.search(r'Weight.*?(\d+)\s*kg', text, re.IGNORECASE)
        if weight_match:
            self.data['patient_info']['weight_kg'] = int(weight_match.group(1))
        
        # Extract test date
        test_date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}:\d{2}', text)
        if test_date_match:
            self.data['patient_info']['test_date'] = test_date_match.group(1)
        
        # Extract test type
        if 'SINGLE' in text.upper() and 'BALANCE' in text.upper():
            if 'RIGHT FOOT' in text.upper():
                self.data['metadata']['test_type'] = 'single_foot_balance'
                self.data['metadata']['foot'] = 'right'
            elif 'LEFT FOOT' in text.upper():
                self.data['metadata']['test_type'] = 'single_foot_balance'
                self.data['metadata']['foot'] = 'left'
        
        # Extract condition
        if 'DYNAMIC' in text.upper():
            self.data['metadata']['condition'] = 'dynamic'
        elif 'STATIC' in text.upper():
            self.data['metadata']['condition'] = 'static'
    
    def _extract_balance_metrics(self, text: str):
        """Extract balance measurement values"""
        metrics = {}
        
        # Total stability index
        stability_match = re.search(r'Total stability index.*?\[.*?\]\s+([\d.]+)', text)
        if stability_match:
            metrics['total_stability_index'] = float(stability_match.group(1))
        
        # Trunk Tot. St. Dev.
        trunk_dev_match = re.search(r'Trunk Tot\.\s*St\.\s*Dev\..*?\[.*?\]\s+([\d.]+)', text)
        if trunk_dev_match:
            metrics['trunk_tot_st_dev'] = float(trunk_dev_match.group(1))
        
        # Sector
        sector_match = re.search(r'Sector.*?\[%\]\s+([\d.]+)', text)
        if sector_match:
            metrics['sector_percentage'] = float(sector_match.group(1))
        
        # Area
        area_match = re.search(r'Area.*?\[%\]\s+([\d.]+)', text)
        if area_match:
            metrics['area_percentage'] = float(area_match.group(1))
        
        # Time
        time_match = re.search(r'Time.*?\[s\]\s+([\d.]+)', text)
        if time_match:
            metrics['time_seconds'] = float(time_match.group(1))
        
        # Score
        score_match = re.search(r'SCORE\s+(\d+)', text)
        if score_match:
            metrics['score'] = float(score_match.group(1))
        
        self.data['balance_metrics'] = metrics
    
    def _extract_trunk_sway(self, text: str):
        """Extract trunk sway measurements"""
        trunk_sway = {}
        
        # Pattern for trunk sway positions (A1, A2, A3, A5, etc.)
        sway_pattern = r'A(\d+)\s*[\n\r\s]*([-\d.]+)?'
        matches = re.finditer(sway_pattern, text)
        
        for match in matches:
            position = f"A{match.group(1)}"
            if match.group(2):
                try:
                    trunk_sway[f'trunk_sway_{position.lower()}'] = float(match.group(2))
                except ValueError:
                    continue
        
        if trunk_sway:
            self.data['balance_metrics'].update(trunk_sway)


def parse_balance_pdf(pdf_path: str) -> Dict:
    """
    Convenience function to parse a balance test PDF
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing extracted data
    """
    parser = BalanceTestParser(pdf_path)
    return parser.parse()
