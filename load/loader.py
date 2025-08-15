"""
Basic loader from structured data to excel.

Assumptions made (should be kept to a minimum):
- There are at least 2 rows of data
- The second row of data is good to use as a "format template"
- If there are rows in which the first column is not a date, they are at the end of the row list.
"""

import datetime
import sys
from typing import Any
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
import openpyxl.utils
from copy import copy
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
  sheet_schema: Any

  def __init__(self, file_path: str, schema_name: str):
    self.schema = schemaManager.get_schema(schema_name)
    if not self.schema:
      raise ValueError(f"No schema found for name: {schema_name}")
    self.file_path = file_path

  def _get_row(self, date: datetime.date):
    """
    Binary search for the row with the given date in the first column.
    If not found, insert a new row in the correct place (sorted by date).
    Returns the row.
    """
    date_column = column_index_from_string(self.sheet_schema.get("fields", {}).get("date", {}).get("column", "A"))

    left = self.sheet_schema.get('headerRowCount', 0) + 1
    right = self.worksheet.max_row

    while left <= right:
      mid = (left + right) // 2
      row = self.worksheet[mid]
      row_date: datetime.date = None
      date_cell = row[date_column];
      if (type(date_cell.value) is datetime.datetime):
        row_date = date_cell.value.date()
      elif (type(date_cell.value) is datetime.date):
        row_date = date_cell.value
      else:
        right -= 1
        continue

      if date == row_date:
        return row
      elif row_date < date:
        left = mid + 1
      else:
        right = mid - 1

    row = self._add_row(left)
    row[date_column].value = date
    return row
  
  def _add_row(self, row_index: int, template_row: int = None):
    """
    Add an empty row at the specified index (push all other rows 1 down).
    Copy styles from the template row (default the first row after the headers).
    """
    if template_row is None:
      template_row = self.sheet_schema.get('headerRowCount', 0) + 2 # use the second row after the header as a template
    self.worksheet.insert_rows(row_index)

    # Copy each cell's style
    for col, src_cell in enumerate(self.worksheet[template_row + 1], start=1): # need to account for the newly added row
      tgt_cell = self.worksheet.cell(row=row_index, column=col)
      if src_cell.has_style:
        tgt_cell.font = copy(src_cell.font)
        tgt_cell.border = copy(src_cell.border)
        tgt_cell.fill = copy(src_cell.fill)
        tgt_cell.number_format = copy(src_cell.number_format)
        tgt_cell.protection = copy(src_cell.protection)
        tgt_cell.alignment = copy(src_cell.alignment)

    # Copy row height
    if self.worksheet.row_dimensions[template_row].height is not None:
      self.worksheet.row_dimensions[row_index].height = self.worksheet.row_dimensions[template_row].height

    # Copy merged cells (same row only)
    for merged_range in list(self.worksheet.merged_cells.ranges):
        min_row, min_col, max_row, max_col = merged_range.bounds
        if min_row == template_row and max_row == template_row:
            new_range = (
                self.worksheet.cell(row=row_index, column=min_col).coordinate
                + ":"
                + self.worksheet.cell(row=row_index, column=max_col).coordinate
            )
            self.worksheet.merge_cells(new_range)

    return self.worksheet[row_index]
  
  def load(self, data: dict):
    self.sheet_schema = self.schema.get('sheets', {}).get(data['type'])
    if not self.sheet_schema:
      raise ValueError(f"No sheet defined for type: {data['type']}")
    
    with WorkbookContext(self.file_path) as self.workbook:
      self.worksheet = self.workbook[self.sheet_schema['name']]
      row = self._get_row(data['sampling_date'].date())
      if not row:
        print(f'No existing row found for date {data["sampling_date"]}', file=sys.stderr)
        return

      for field, field_schema in self.sheet_schema.get('fields', {}).items():
        if field in data["results"]:
          col_index = column_index_from_string(field_schema['column'])
          row[col_index].value = data["results"][field]
