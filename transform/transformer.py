"""
Basic transformer from the extracted data to a structured format.

Assumptions made (should be kept to a minimum):
"""

from datetime import datetime
import sys
from .schemas import TransformSchemaManager
schemaManager = TransformSchemaManager()

class Transformer:

  sampling_date: datetime
  results: dict

  def __init__(self, schema_name: str, data: dict):
    self.schema = schemaManager.get_schema(schema_name)
    if not self.schema:
      raise ValueError(f"No schema found for name: {schema_name}")
    self.input_data = data
    self._transform()

  def _transform(self) -> dict:
    if not self.schema:
      raise ValueError("Schema is not defined for transformation")
    if not self.input_data:
      raise ValueError("Input data cannot be empty")
    self._transform_sampling_date()
    self._transform_results_table()
    
  def _transform_sampling_date(self) -> None:
    date_format = self.schema.get('dateFormat', "%d/%m/%y")
    if 'sampling_date' in self.input_data:
      try:
        self.sampling_date = datetime.strptime(self.input_data['sampling_date'], date_format)
      except ValueError as e:
        raise ValueError(f"Invalid sampling date format: {e}")
    else:
      raise ValueError("Sampling date not found in input data")
    
  def _transform_results_table(self):
    results_schema = self.schema.get("tables").get("results")
    if not results_schema:
      raise ValueError("Results table schema is not defined")
    results_table = self.input_data.get('tables', {}).get('results', [])

    self.results = {}

    test_names = results_schema.get('testNames', {})
    for row in results_table:
      test_name = row.get('testName')
      if test_name in test_names:
        value = row.get('result')
        try:
          value = float(value)
        except (ValueError, TypeError):
          print(f"Value for test '{test_name}' is not a valid number: {value}", file=sys.stderr)
        self.results[test_names[test_name]] = value
      else:
        print(f"Test name '{test_name}' not found in schema", file=sys.stderr)
