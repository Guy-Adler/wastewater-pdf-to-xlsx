"""
Basic loader from structured data to excel.

Assumptions made (should be kept to a minimum):
- The date exists in the excel file
"""

import datetime
import sys
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
import openpyxl.utils
from .schemas import LoadSchemaManager
from .utils import WorkbookContext

def column_index_from_string(col_letter: str) -> int:
  return openpyxl.utils.column_index_from_string(col_letter) - 1

schemaManager = LoadSchemaManager()

class Loader:

  file_path: str
  workbook: Workbook
  worksheet: Worksheet
  schema: dict

  def __init__(self, file_path: str, schema_name: str):
    self.schema = schemaManager.get_schema(schema_name)
    if not self.schema:
      raise ValueError(f"No schema found for name: {schema_name}")
    self.file_path = file_path
  
  def load(self, data: dict):
    sheet_schema = self.schema.get('sheets', {}).get(data['type'])
    if not sheet_schema:
      raise ValueError(f"No sheet defined for type: {data['type']}")
    
    with WorkbookContext(self.file_path) as self.workbook:
      self.worksheet = self.workbook[sheet_schema['name']]
      row = None
      for _row in self.worksheet.iter_rows(min_row=sheet_schema.get('headerRowCount', 0) + 1):
        if (type(_row[0].value) is datetime.datetime and _row[0].value.date() == data['sampling_date'].date()):
          row = _row
          break
      
      if not row:
        print(f'No existing row found for date {data["sampling_date"]}', sys.stderr)
        return

      for field, field_schema in sheet_schema.get('fields', {}).items():
        if field in data["results"]:
          col_index = column_index_from_string(field_schema['column'])
          row[col_index].value = data["results"][field]
