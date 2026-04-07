"""
Example Script: Import EMG Data from PDF files
"""
import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion.emg_parser import parse_noraxon_pdf
from database.connection import SessionLocal, init_db
from database.models import Patient, EMGSession, EMGData
from datetime import datetime


def import_emg_pdfs(pdf_directory: str):
    """Import all EMG PDFs from a directory"""
    # Initialize database
    init_db()
    db = SessionLocal()
    
    # Find all PDF files
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_directory}")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    print()
    
    for pdf_path in pdf_files:
        try:
            print(f"Processing: {os.path.basename(pdf_path)}")
            
            # Parse PDF
            data = parse_noraxon_pdf(pdf_path)
            
            # Find or create patient
            patient_name = data['patient_info'].get('name', 'Unknown')
            patient = db.query(Patient).filter(Patient.name == patient_name).first()
            
            if not patient:
                patient = Patient(
                    patient_id=patient_name.replace(' ', '_'),
                    name=patient_name,
                    date_of_birth=data['patient_info'].get('test_date', datetime.utcnow())
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
                print(f"  ✅ Created patient: {patient_name}")
            else:
                print(f"  ℹ️  Found existing patient: {patient_name}")
            
            # Create EMG session
            session = EMGSession(
                patient_id=patient.id,
                session_date=data['patient_info'].get('test_date', datetime.utcnow()),
                stage=data['metadata'].get('stage', 'Unknown'),
                frequency_hz=2000,
                equipment="Noraxon"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            
            # Add EMG measurements
            for measurement in data['emg_measurements']:
                emg_data = EMGData(
                    session_id=session.id,
                    muscle_name=measurement['muscle_name'],
                    side=measurement.get('side'),
                    min_value=measurement.get('min_value'),
                    max_value=measurement.get('max_value'),
                    mean_value=measurement.get('mean_value')
                )
                db.add(emg_data)
            
            db.commit()
            print(f"  ✅ Imported {len(data['emg_measurements'])} measurements")
            print()
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()
            continue
    
    db.close()
    print("✅ Import complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import EMG data from PDF files')
    parser.add_argument('--path', type=str, required=True, help='Directory containing PDF files')
    
    args = parser.parse_args()
    import_emg_pdfs(args.path)
