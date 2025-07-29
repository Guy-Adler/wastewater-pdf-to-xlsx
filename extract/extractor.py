"""
Basic Pdf Extractor

Assumptions made (should be kept to a minimum):
- 1 page only
"""

import pdfplumber
import re
from typing import List
from datetime import datetime
from bidi.algorithm import get_display
from utils import ExtractedTables
from .schemas import ExtractSchemaManager

def fix_rtl_text(cell: str):
  return get_display(cell)

schemaManager = ExtractSchemaManager()

class PdfExtractor:
  pdf_path: str
  _pdf: pdfplumber.PDF
  _pdf_content: str

  sampling_date: datetime
  tables: dict[str, List[dict[str, str | None]]]
  schemaName: str
  schema: dict

  def __init__(self, pdf_path: str):
    self.pdf_path = pdf_path
    self.tables = {}
    self._extract_data()

  def _extract_data(self) -> ExtractedTables:
    with pdfplumber.open(self.pdf_path) as self._pdf:
      self._pdf_content = fix_rtl_text(self._pdf.pages[0].extract_text())

      # Determine which schema to use
      self.schemaName = schemaManager.find_matching_schema(self._pdf_content)
      if self.schemaName:
        print(f"Using schema: {self.schemaName}")
        self.schema = schemaManager.schemas[self.schemaName]
      else:
        raise ValueError("No matching schema found for the PDF content")
      
      self._extract_sampling_date()
      self._extract_tables()

  def _extract_sampling_date(self) -> None:
    date_format = self.schema.get('dateFormat', "%d/%m/%y")
    sampling_date_extraction_regex = self.schema.get('samplingDateExtractionRegex', None)
    if sampling_date_extraction_regex:
      pattern = re.compile(sampling_date_extraction_regex)
    else:
      raise ValueError("No sampling date extraction regex defined in the schema")
    
    
    sampling_date = pattern.search(self._pdf_content)
    if sampling_date:
      sampling_date =sampling_date.group('date')
    else:
      raise ValueError("No sampling date found in the PDF content")
    
    self.sampling_date = datetime.strptime(sampling_date, date_format)


  def _extract_tables(self) -> None:
    tables_schema = self.schema.get('tables')
    if not tables_schema:
      return
    
    tables: ExtractedTables = []
    page_tables = self._pdf.pages[0].extract_tables()
    for table in page_tables:
      processed_table = []
      for row in table:
        processed_row = []
        for cell in row:
          processed_cell = fix_rtl_text(cell) if cell is not None else None
          processed_row.append(processed_cell)
        processed_table.append(processed_row)
      tables.append(processed_table)

    for table_name, table_schema in tables_schema.items():
      table = tables[table_schema['tableNumber']]
      headers = table[:table_schema.get('headerRowCount', 0)]
      data = table[table_schema.get('headerRowCount', 0):]

      columns_schema: dict[int, List[str]] = table_schema.get('columns')
      if columns_schema is None:
        raise ValueError(f"No columns schema defined for table '{table_name}' in the schema '{self.schemaName}'")
      
      if isinstance(columns_schema, dict):
        columns_schema = { int(k): v for k, v in columns_schema.items() }

      if isinstance(columns_schema, list):
        columns_schema = { len(columns_schema): columns_schema }

      if len(data) == 0:
        self.tables[table_name] = []
        return
      
      if len(data[0]) not in columns_schema.keys():
        raise ValueError(f"Table '{table_name}' in schema '{self.schemaName}' has no matching columns for the data extracted")
      
      columns_schema = columns_schema[len(data[0])]

      self.tables[table_name] = []
      for row in data:
        processed_row = {}
        for col_index, col_name in enumerate(columns_schema):
          processed_row[col_name] = row[col_index]
        self.tables[table_name].append(processed_row)