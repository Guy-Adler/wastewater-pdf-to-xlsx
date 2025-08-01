#!.venv/bin/python3

import os
import io
import sys
import tempfile
import traceback
import urllib.parse
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from extract import PdfExtractor
from transform import Transformer
from load import Loader

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files or 'xlsx_file' not in request.files:
        return {'error': 'Both PDF and XLSX files are required'}, 400

    pdf_file = request.files['pdf_file']
    xlsx_file = request.files['xlsx_file']
    
    # Check if files were selected
    if pdf_file.filename == '' or xlsx_file.filename == '':
        return {'error': 'Both PDF and XLSX files must be selected'}, 400
    
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
            pdf_extractor = PdfExtractor(pdf_temp_path)
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
            
            loader = Loader(xlsx_temp_path, 'acre')
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