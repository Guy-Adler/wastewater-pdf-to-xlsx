#!.venv/bin/python3

import os
import sys
import tempfile
import traceback
from flask import Flask, render_template, request, send_file
from extract import PdfExtractor
from transform import Transformer
from load import Loader
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def get_available_schemas():
    """Get available schemas for the select fields"""
    schemas = {
        'waste_treatment_plants': {},
        'labs': {}
    }
    
    # Read load schemas (waste treatment plants)
    load_dir = "schemas/load"
    if os.path.exists(load_dir):
        for filename in os.listdir(load_dir):
            if filename.endswith(".json"):
                schema_name = filename.removesuffix('.json')
                try:
                    with open(os.path.join(load_dir, filename), "r", encoding="utf-8") as f:
                        schema = json.load(f)
                        display_name = schema.get('name')
                        if display_name is not None:
                            schemas['waste_treatment_plants'][schema_name] = display_name
                except Exception as e:
                    print(f"Error reading schema {filename}: {e}")
    
    # Read extract schemas (labs)
    extract_dir = "schemas/extract"
    if os.path.exists(extract_dir):
        for filename in os.listdir(extract_dir):
            if filename.endswith(".json"):
                schema_name = filename.removesuffix('.json')
                try:
                    with open(os.path.join(extract_dir, filename), "r", encoding="utf-8") as f:
                        schema = json.load(f)
                        display_name = schema.get('name')
                        if display_name is not None:
                            schemas['labs'][schema_name] = display_name
                except Exception as e:
                    print(f"Error reading schema {filename}: {e}")
    
    return schemas

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    schemas = get_available_schemas()
    return render_template('index.html', schemas=schemas)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files or 'xlsx_file' not in request.files:
        return {'error': 'Both PDF and XLSX files are required'}, 400

    pdf_file = request.files['pdf_file']
    xlsx_file = request.files['xlsx_file']
    
    # Get the selected waste treatment plant and lab name
    load_schema_name = request.form.get('waste_treatment_plant')
    extract_schema_name = request.form.get('lab_name')
    
    # Check if files were selected
    if pdf_file.filename == '' or xlsx_file.filename == '':
        return {'error': 'Both PDF and XLSX files must be selected'}, 400
    
    # Check if waste treatment plant and lab name were selected
    if not load_schema_name:
        return {'error': 'Waste treatment plant must be selected'}, 400
    
    if not extract_schema_name:
        return {'error': 'Lab name must be selected'}, 400
   
    # Check file extensions
    if not (pdf_file and allowed_file(pdf_file.filename) and 
            pdf_file.filename.lower().endswith('.pdf')):
        return {'error': 'Invalid PDF file'}, 400
    
    if not (xlsx_file and allowed_file(xlsx_file.filename) and 
            xlsx_file.filename.lower().endswith(('.xlsx', '.xls'))):
        return {'error': 'Invalid XLSX/XLS file'}, 400
    
    try:
        # Read files into memory
        pdf_content = pdf_file.read()
        xlsx_content = xlsx_file.read()
        
        # Create temporary files for processing
        pdf_tmp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        pdf_temp_path = pdf_tmp_file.name
        pdf_temp = open(pdf_tmp_file.name, 'wb')
        pdf_temp.write(pdf_content)
        pdf_temp.flush()
        pdf_temp.seek(0)

        xlsx_tmp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        xlsx_temp_path = xlsx_tmp_file.name
        xlsx_temp = open(xlsx_tmp_file.name, 'wb')
        xlsx_temp.write(xlsx_content)
        xlsx_temp.flush()
        xlsx_temp.seek(0)
        
        try:
            # Process the files using existing code
            pdf_extractor = PdfExtractor(pdf_temp_path, extract_schema_name)
            extracted_data = {
                "sampling_date": pdf_extractor.sampling_date,
                "tables": pdf_extractor.tables,
                "type": pdf_extractor.type,
            }
            
            transformer = Transformer(pdf_extractor.schemaName, extracted_data)
            
            transformed_data = {
                "type": extracted_data["type"],
                "sampling_date": transformer.sampling_date,
                "results": transformer.results,
            }
            
            loader = Loader(xlsx_temp_path, load_schema_name)
            loader.load(transformed_data)
            
            # Return the processed file with proper headers
            response = send_file(
                xlsx_temp_path,
                as_attachment=True,
                download_name=xlsx_file.filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                max_age=0
            )
            
            # Let Flask handle the filename encoding automatically
            return response
                    
        finally:
            # Clean up temporary input files
            if os.path.exists(pdf_temp_path):
                os.unlink(pdf_temp_path)
            if os.path.exists(xlsx_temp_path):
                os.unlink(xlsx_temp_path)
        
    except Exception as e:
        print(traceback.format_exc(), file=sys.stderr)
        return {'error': f'Error processing files: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)