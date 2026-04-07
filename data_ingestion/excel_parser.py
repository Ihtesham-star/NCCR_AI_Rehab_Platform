"""
Excel Data Parser for Clinical Tests and EMG Stage Data - FULLY FIXED
Handles Excel files containing patient demographics, clinical tests, and stage-based measurements
FIXED: Now properly extracts clinical test values from your Excel format
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import re


class ClinicalDataParser:
    """Parser for clinical test data from Excel files"""
    
    def __init__(self, excel_path: str, sheet_name: Optional[str] = None):
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        self.data = {
            'patients': [],
            'clinical_tests': [],
            'emg_sessions': []
        }
    
    def parse(self) -> Dict:
        """Parse Excel file and extract all data"""
        try:
            # Read Excel file
            if self.sheet_name:
                df = pd.read_excel(self.excel_path, sheet_name=self.sheet_name)
            else:
                # Read all sheets
                excel_file = pd.ExcelFile(self.excel_path)
                for sheet in excel_file.sheet_names:
                    self._parse_sheet(sheet)
                return self.data
            
            self._parse_dataframe(df)
            return self.data
        
        except Exception as e:
            raise Exception(f"Error parsing Excel file: {str(e)}")
    
    def _parse_sheet(self, sheet_name: str):
        """Parse a specific sheet"""
        df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
        self._parse_dataframe(df, sheet_name)
    
    def _parse_dataframe(self, df: pd.DataFrame, sheet_name: str = None):
        """Parse dataframe based on its structure"""
        # Convert column names to string and print for debugging
        print(f"Parsing sheet: {sheet_name}")
        print(f"Columns found: {list(df.columns)}")
        print(f"First row data: {df.iloc[0].to_dict() if len(df) > 0 else 'Empty'}")
        
        # Check if this is a stage EMG file by looking at the sheet name FIRST
        if sheet_name and ('stage' in str(sheet_name).lower() or 'ulan' in str(sheet_name).lower()):
            print("Detected STAGE EMG sheet (from filename)")
            self._parse_stage_emg_data(df, sheet_name)
            return
        
        # Make column matching more flexible - check for partial matches
        columns_str = str(df.columns).lower()
        
        # Check if it's a perturbation project sheet (has patient demographics columns)
        if 'children' in columns_str and 'age' in columns_str and 'height' in columns_str:
            print("Detected patient demographics sheet")
            self._parse_perturbation_data(df)
        
        # Check if it's an Amina-type detailed measurement sheet
        elif 'activities' in columns_str or 'force' in columns_str:
            print("Detected detailed EMG sheet")
            self._parse_stage_emg_data(df, sheet_name)
        
        else:
            print(f"Unknown format. Trying generic parsing...")
            # Try generic parsing - look for any patient-like data
            self._parse_generic_data(df)
    
    def _parse_perturbation_data(self, df: pd.DataFrame):
        """Parse perturbation project data with patient demographics and clinical tests"""
        
        # ✅ FIXED: Normalize column names - make flexible matching
        col_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Patient info columns
            if 'children' in col_lower and 'name' in col_lower:
                col_mapping['children_name'] = col
            elif col_lower == 'age':
                col_mapping['age'] = col
            elif 'height' in col_lower:
                col_mapping['height'] = col
            elif 'weight' in col_lower:
                col_mapping['weight'] = col
            elif 'gmfc' in col_lower:  # GMFCs or GMFCS
                col_mapping['gmfcs'] = col
            elif col_lower == 'date' or col_lower == 'dob':
                col_mapping['date'] = col
            
            # ✅ FIXED: Clinical test columns with more flexible matching
            elif '6' in col_lower and ('mwt' in col_lower or 'mw' in col_lower or 'minute' in col_lower or 'walk' in col_lower):
                col_mapping['6mwt'] = col
            elif '10' in col_lower and ('mwt' in col_lower or 'walk' in col_lower):
                col_mapping['10mwt'] = col
            elif 'tug' in col_lower or 'time up' in col_lower or 'time and go' in col_lower or 'up and go' in col_lower:
                col_mapping['tug'] = col
            elif 'gmfm' in col_lower and 'cs' not in col_lower:
                col_mapping['gmfm'] = col
            elif 'who' in col_lower or 'qol' in col_lower:
                col_mapping['who_qol'] = col
            elif 'omni' in col_lower:
                col_mapping['omni'] = col
            # ✅ FIXED: Add Modified Ashworth scale
            elif 'ashworth' in col_lower or 'modified ashworth' in col_lower:
                col_mapping['modified_ashworth'] = col
        
        print(f"✅ Column mapping: {col_mapping}")
        
        for idx, row in df.iterrows():
            # Skip header rows or empty rows
            date_col = col_mapping.get('date', 'Date')
            if pd.isna(row.get(date_col)) or row.get(date_col) == 'Date':
                continue
            
            try:
                # Extract patient name
                name_col = col_mapping.get('children_name', 'Children Name')
                patient_name_raw = str(row.get(name_col, '')).strip()
                
                print(f"Row {idx}: Checking name = '{patient_name_raw}'")
                
                if not patient_name_raw or patient_name_raw == '' or patient_name_raw == 'nan':
                    print(f"  -> Skipping: empty name")
                    continue
                
                # Skip if this is the header row itself
                if 'children' in patient_name_raw.lower() and 'name' in patient_name_raw.lower():
                    print(f"  -> Skipping: header row")
                    continue
                
                # Extract ID from name like "Kyzzhuldyz (ID:K15)" or "Batyrkhan (ID:B17)"
                patient_name = patient_name_raw
                patient_id = None
                
                # Skip if this looks like a test item instead of a patient name
                if re.match(r'^\d+\.', patient_name_raw):
                    print(f"  -> Skipping test item (not a patient): {patient_name_raw}")
                    continue
                
                # Check if name contains (ID:xxx) pattern
                id_match = re.search(r'\(ID:([^)]+)\)', patient_name_raw, re.IGNORECASE)
                if id_match:
                    patient_id = id_match.group(1).strip()
                    # Remove the (ID:xxx) part from the name
                    patient_name = re.sub(r'\s*\(ID:[^)]+\)', '', patient_name_raw).strip()
                    print(f"  -> Extracted: name='{patient_name}', id='{patient_id}'")
                else:
                    # No ID found, use name as ID
                    patient_id = patient_name_raw.replace(' ', '_')
                    print(f"  -> No ID found, using name as ID: '{patient_id}'")
                
                # Extract patient info
                patient_data = {
                    'name': patient_name,
                    'patient_id': patient_id,
                }
                
                # Age
                if 'age' in col_mapping and not pd.isna(row.get(col_mapping['age'])):
                    try:
                        patient_data['age'] = int(row[col_mapping['age']])
                    except:
                        pass
                
                # Height
                if 'height' in col_mapping and not pd.isna(row.get(col_mapping['height'])):
                    try:
                        height_val = str(row[col_mapping['height']]).replace('cm', '').strip()
                        patient_data['height_cm'] = float(height_val)
                    except:
                        pass
                
                # Weight
                if 'weight' in col_mapping and not pd.isna(row.get(col_mapping['weight'])):
                    try:
                        weight_val = str(row[col_mapping['weight']]).replace('kg', '').replace('kgs', '').strip()
                        patient_data['weight_kg'] = float(weight_val)
                    except:
                        pass
                
                # Calculate date of birth from age
                if 'age' in patient_data and patient_data['age']:
                    current_year = datetime.now().year
                    birth_year = current_year - patient_data['age']
                    patient_data['date_of_birth'] = datetime(birth_year, 1, 1)
                else:
                    # Use test date if available
                    dob = None
                    if 'date' in col_mapping and not pd.isna(row.get(col_mapping['date'])):
                        try:
                            dob = pd.to_datetime(row[col_mapping['date']])
                        except:
                            pass
                    patient_data['date_of_birth'] = dob if dob else datetime.now()
                
                # Extract GMFCS level
                if 'gmfcs' in col_mapping and not pd.isna(row.get(col_mapping['gmfcs'])):
                    gmfcs_str = str(row[col_mapping['gmfcs']]).lower()
                    level_match = re.search(r'(\d+)', gmfcs_str)
                    if level_match:
                        patient_data['gmfcs_level'] = int(level_match.group(1))
                
                self.data['patients'].append(patient_data)
                print(f"✅ Added patient: {patient_data['name']} - Height: {patient_data.get('height_cm')} cm, Weight: {patient_data.get('weight_kg')} kg, GMFCS: {patient_data.get('gmfcs_level')}")
                
                # ✅ FIXED: Extract clinical test data
                test_date = datetime.now()
                if 'date' in col_mapping and not pd.isna(row.get(col_mapping['date'])):
                    try:
                        test_date = pd.to_datetime(row[col_mapping['date']])
                    except:
                        test_date = datetime.now()
                
                clinical_test = {
                    'patient_id': patient_data['patient_id'],
                    'test_date': test_date,
                    'test_type': 'CLINICAL_BATTERY'
                }
                
                # ✅ FIXED: 6MWT - can be time OR distance
                if '6mwt' in col_mapping and not pd.isna(row.get(col_mapping['6mwt'])):
                    mwt_val = str(row[col_mapping['6mwt']]).strip()
                    print(f"  6MWT value: '{mwt_val}'")
                    try:
                        # If it contains "meter" or is a number, it's distance
                        if 'meter' in mwt_val.lower():
                            distance = float(re.search(r'([\d.]+)', mwt_val).group(1))
                            clinical_test['distance_6mwt_meters'] = distance
                            print(f"    -> Extracted distance: {distance} meters")
                        # If it contains "minute" or ":" it's time - we'll just note it
                        elif 'minute' in mwt_val.lower() or ':' in mwt_val:
                            print(f"    -> Time format detected: {mwt_val} (storing as note)")
                            # Store time in seconds if possible
                            time_match = re.search(r'(\d+):(\d+)', mwt_val)
                            if time_match:
                                minutes = int(time_match.group(1))
                                seconds = int(time_match.group(2))
                                clinical_test['time_6mwt_seconds'] = minutes * 60 + seconds
                                print(f"    -> Converted to seconds: {clinical_test['time_6mwt_seconds']}")
                        else:
                            # Try as plain number (assume meters)
                            clinical_test['distance_6mwt_meters'] = float(mwt_val)
                            print(f"    -> Parsed as meters: {clinical_test['distance_6mwt_meters']}")
                    except Exception as e:
                        print(f"    -> Failed to parse 6MWT: {e}")
                
                # ✅ FIXED: 10MWT
                if '10mwt' in col_mapping and not pd.isna(row.get(col_mapping['10mwt'])):
                    mwt_value = str(row[col_mapping['10mwt']]).strip()
                    print(f"  10MWT value: '{mwt_value}'")
                    try:
                        # Extract number, ignore "sec" text
                        number = re.search(r'([\d.]+)', mwt_value)
                        if number:
                            clinical_test['time_10mwt_seconds'] = float(number.group(1))
                            print(f"    -> Extracted: {clinical_test['time_10mwt_seconds']} seconds")
                    except Exception as e:
                        print(f"    -> Failed to parse 10MWT: {e}")
                
                # ✅ FIXED: Time up and go test (TUG)
                if 'tug' in col_mapping and not pd.isna(row.get(col_mapping['tug'])):
                    tug_value = str(row[col_mapping['tug']]).strip()
                    print(f"  TUG value: '{tug_value}'")
                    try:
                        # Extract number
                        number = re.search(r'([\d.]+)', tug_value)
                        if number:
                            clinical_test['tug_time_seconds'] = float(number.group(1))
                            print(f"    -> Extracted: {clinical_test['tug_time_seconds']} seconds")
                    except Exception as e:
                        print(f"    -> Failed to parse TUG: {e}")
                
                # ✅ FIXED: GMFM score
                if 'gmfm' in col_mapping and not pd.isna(row.get(col_mapping['gmfm'])):
                    gmfm_val = str(row[col_mapping['gmfm']]).strip()
                    print(f"  GMFM value: '{gmfm_val}'")
                    try:
                        if '%' in gmfm_val:
                            clinical_test['gmfm_score'] = float(gmfm_val.replace('%', ''))
                        else:
                            gmfm_float = float(gmfm_val)
                            if gmfm_float < 1.0:
                                clinical_test['gmfm_score'] = gmfm_float * 100
                            else:
                                clinical_test['gmfm_score'] = gmfm_float
                        print(f"    -> Extracted: {clinical_test['gmfm_score']}%")
                    except Exception as e:
                        print(f"    -> Failed to parse GMFM: {e}")
                
                # ✅ FIXED: WHO-QOL
                if 'who_qol' in col_mapping and not pd.isna(row.get(col_mapping['who_qol'])):
                    try:
                        clinical_test['who_qol_score'] = float(row[col_mapping['who_qol']])
                        print(f"  WHO-QOL: {clinical_test['who_qol_score']}")
                    except Exception as e:
                        print(f"  Failed to parse WHO-QOL: {e}")
                
                # ✅ FIXED: OMNI exertion scale
                if 'omni' in col_mapping and not pd.isna(row.get(col_mapping['omni'])):
                    try:
                        clinical_test['omni_exertion_scale'] = int(row[col_mapping['omni']])
                        print(f"  OMNI: {clinical_test['omni_exertion_scale']}")
                    except Exception as e:
                        print(f"  Failed to parse OMNI: {e}")
                
                # ✅ FIXED: Modified Ashworth Scale
                if 'modified_ashworth' in col_mapping and not pd.isna(row.get(col_mapping['modified_ashworth'])):
                    try:
                        ashworth_val = str(row[col_mapping['modified_ashworth']]).strip()
                        # Extract number
                        number = re.search(r'([\d]+)', ashworth_val)
                        if number:
                            clinical_test['modified_ashworth_scale'] = int(number.group(1))
                            print(f"  Modified Ashworth: {clinical_test['modified_ashworth_scale']}")
                    except Exception as e:
                        print(f"  Failed to parse Modified Ashworth: {e}")
                
                # Only add if we have actual test data (beyond patient_id and date)
                if len(clinical_test) > 3:  # Has data beyond patient_id, date, and test_type
                    self.data['clinical_tests'].append(clinical_test)
                    print(f"✅ Added clinical test with {len(clinical_test)-3} measurements")
                else:
                    print(f"⚠️  No test data extracted for this patient")
            
            except Exception as e:
                print(f"❌ Error parsing row {idx}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
    
    def _parse_stage_emg_data(self, df: pd.DataFrame, sheet_name: str):
        """Parse Ulan stage EMG data"""
        print(f"Parsing stage EMG data from sheet: {sheet_name}")
        
        # Extract patient name from first row
        patient_name = None
        if len(df) > 0:
            first_row = df.iloc[0]
            if len(first_row) > 1 and isinstance(first_row.iloc[1], str):
                patient_name = first_row.iloc[1].strip()
                print(f"Found patient name: {patient_name}")
        
        # Extract frequency from row 2
        frequency_hz = 2000  # default
        if len(df) > 1:
            freq_row = df.iloc[1]
            if len(freq_row) > 1:
                try:
                    frequency_hz = int(freq_row.iloc[1])
                    print(f"Found frequency: {frequency_hz} Hz")
                except:
                    pass
        
        # Extract date from row 3
        test_date = datetime.now()
        if len(df) > 2:
            date_row = df.iloc[2]
            if len(date_row) > 1:
                try:
                    test_date = pd.to_datetime(date_row.iloc[1])
                    print(f"Found date: {test_date}")
                except:
                    pass
        
        # Create patient if we have a name
        if patient_name:
            patient_data = {
                'name': patient_name,
                'patient_id': patient_name.replace(' ', '_'),
                'date_of_birth': test_date
            }
            self.data['patients'].append(patient_data)
            print(f"Created patient: {patient_data}")
        
        # Extract stage info from sheet name
        stage = sheet_name if sheet_name else 'Unknown'
        
        emg_session = {
            'patient_name': patient_name or 'Unknown',
            'stage': stage,
            'frequency_hz': frequency_hz,
            'test_date': test_date,
            'measurements': []
        }
        
        self.data['emg_sessions'].append(emg_session)
        print(f"Created EMG session for stage: {stage}")
    
    def _parse_detailed_emg_data(self, df: pd.DataFrame, sheet_name: str):
        """Parse detailed EMG data with muscle-specific measurements"""
        pass
    
    def _parse_generic_data(self, df: pd.DataFrame):
        """Generic parser for any Excel with patient-like data"""
        print("Using generic parser...")
        
        # Look for first non-empty row with data
        for idx, row in df.iterrows():
            if idx > 20:  # Don't search too far
                break
            
            # Look for anything that looks like a name
            for col in df.columns:
                value = row[col]
                if pd.isna(value) or value == col:
                    continue
                
                # If we find text that looks like a name (has letters and spaces)
                if isinstance(value, str) and len(value) > 3 and ' ' in value:
                    print(f"Found potential patient name: {value}")
                    
                    patient_data = {
                        'name': value.strip(),
                        'patient_id': value.replace(' ', '_').strip(),
                        'date_of_birth': datetime.now()
                    }
                    
                    # Look for other fields in the same row
                    for other_col in df.columns:
                        other_val = row[other_col]
                        if pd.isna(other_val):
                            continue
                        
                        col_name_lower = str(other_col).lower()
                        
                        # Try to match fields
                        if 'age' in col_name_lower and str(other_val).isdigit():
                            patient_data['age'] = int(other_val)
                        elif 'height' in col_name_lower:
                            try:
                                patient_data['height_cm'] = float(other_val)
                            except:
                                pass
                        elif 'weight' in col_name_lower:
                            try:
                                patient_data['weight_kg'] = float(other_val)
                            except:
                                pass
                    
                    self.data['patients'].append(patient_data)
                    print(f"Added patient: {patient_data}")
                    break


def parse_clinical_excel(excel_path: str, sheet_name: Optional[str] = None) -> Dict:
    """
    Convenience function to parse clinical Excel file
    
    Args:
        excel_path: Path to Excel file
        sheet_name: Specific sheet to parse (optional)
    
    Returns:
        Dictionary containing extracted data
    """
    parser = ClinicalDataParser(excel_path, sheet_name)
    return parser.parse()