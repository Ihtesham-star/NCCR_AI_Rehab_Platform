"""
PDF Parser for Noraxon EMG Reports
Extracts muscle activity data from Noraxon Quick Analysis PDFs
"""
import re
from typing import Dict, List, Optional
from datetime import datetime
import pdfplumber


class NoraxonEMGParser:
    """Parser for Noraxon EMG PDF reports"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.data = {
            'patient_info': {},
            'emg_measurements': [],
            'metadata': {}
        }
    
    def parse(self) -> Dict:
        """Parse the entire PDF and extract all data"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                full_text = ""
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                    
                    # Extract patient information
                    self._extract_patient_info(text)
                    
                    # Extract EMG measurements
                    self._extract_emg_measurements(text)
                    
                    # Extract tables if available
                    tables = page.extract_tables()
                    if tables:
                        self._extract_table_data(tables)
                
                # Debug output
                print(f"Parsed EMG PDF: {self.pdf_path}")
                print(f"Patient info: {self.data['patient_info']}")
                print(f"EMG measurements found: {len(self.data['emg_measurements'])}")
                print(f"First 500 chars of text:\n{full_text[:500]}")
            
            return self.data
        
        except Exception as e:
            print(f"Error parsing EMG PDF: {str(e)}")
            raise Exception(f"Error parsing Noraxon PDF: {str(e)}")
    
    def _extract_patient_info(self, text: str):
        """Extract patient information from text"""
        # Extract patient name
        name_match = re.search(r'Name\s+([A-Z\s]+)', text)
        if name_match:
            self.data['patient_info']['name'] = name_match.group(1).strip()
        
        # Extract date
        date_match = re.search(r'Record.*?(\d{1,2}/\d{1,2}/\d{4})', text)
        if date_match:
            date_str = date_match.group(1)
            self.data['patient_info']['test_date'] = datetime.strptime(date_str, '%m/%d/%Y')
        
        # Extract stage information
        stage_match = re.search(r'Stage\s*(\d+)\s*(upper|lower)', text, re.IGNORECASE)
        if stage_match:
            self.data['metadata']['stage'] = f"Stage{stage_match.group(1)}_{stage_match.group(2)}"
    
    def _extract_emg_measurements(self, text: str):
        """Extract EMG measurement values from text"""
        # Pattern to match muscle data: Muscle Name, Min, Max, Mean
        patterns = [
            # Pattern for lines like: "Faroi LT.N    1.536    285.7    65.78"
            r'([A-Z\s\.]+[LT|RT][\.,_][A-Z]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)',
            # Pattern for full muscle names
            r'(BICEPS|GLUT|VLO|TIB|MED|GASTRO|ADDUCTORS)[\s\.]+(FEM|MED|MAX|ANT|GAS)?[\s\.]*(LT|RT)[,\._]?[A-Za-z]*\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                muscle_data = {
                    'muscle_name': self._normalize_muscle_name(match.group(1)),
                    'min_value': float(match.group(2) if len(match.groups()) > 3 else match.group(4)),
                    'max_value': float(match.group(3) if len(match.groups()) > 3 else match.group(5)),
                    'mean_value': float(match.group(4) if len(match.groups()) > 3 else match.group(6))
                }
                
                # Determine side
                if 'LT' in muscle_data['muscle_name']:
                    muscle_data['side'] = 'LT'
                elif 'RT' in muscle_data['muscle_name']:
                    muscle_data['side'] = 'RT'
                
                self.data['emg_measurements'].append(muscle_data)
    
    def _extract_table_data(self, tables: List):
        """Extract data from tables if present"""
        for table in tables:
            if not table:
                continue
            
            # Assume first row is header
            if len(table) > 1:
                headers = table[0]
                
                # Look for columns: Muscle, Minimum, Maximum, Mean
                for row in table[1:]:
                    if len(row) >= 4 and row[0]:
                        try:
                            muscle_data = {
                                'muscle_name': self._normalize_muscle_name(row[0]),
                                'min_value': float(row[1]) if row[1] else None,
                                'max_value': float(row[2]) if row[2] else None,
                                'mean_value': float(row[3]) if row[3] else None
                            }
                            
                            # Avoid duplicates
                            if not any(m['muscle_name'] == muscle_data['muscle_name'] 
                                      for m in self.data['emg_measurements']):
                                self.data['emg_measurements'].append(muscle_data)
                        except (ValueError, TypeError):
                            continue
    
    def _normalize_muscle_name(self, muscle_str: str) -> str:
        """Normalize muscle name to standard format"""
        # Remove extra spaces and convert to uppercase
        normalized = re.sub(r'\s+', '_', muscle_str.strip().upper())
        
        # Standardize common variations
        replacements = {
            'FAROI': 'BICEPS_FEM',
            'V.L.O': 'VLO',
            'V_L_O': 'VLO',
            'TIB.ANT': 'TIB_ANT',
            'TIB_ANT': 'TIB_ANT',
            'MED.GAS': 'MED_GAS',
            'MED_GAS': 'MED_GAS',
            '.': '_',
            ',': '_'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized


def parse_noraxon_pdf(pdf_path: str) -> Dict:
    """
    Convenience function to parse a Noraxon EMG PDF
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing extracted data
    """
    parser = NoraxonEMGParser(pdf_path)
    return parser.parse()
