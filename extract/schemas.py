""""
Schema utilities for PDF extraction.
"""
import os
import json
import re

class ExtractSchemaManager:
  _instance = None
  schemas: dict

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance
  
  def __init__(self):
    if not hasattr(self, 'schemas'):
      self.load_schemas()

  def load_schemas(self):
    """
    Load and return the schemas for PDF extraction.
    """

    self.schemas = {}
    schemas_dir = "schemas/extract"
    for filename in os.listdir(schemas_dir):
      if filename.endswith(".json"):
        with open(os.path.join(schemas_dir, filename), "r", encoding="utf-8") as f:
          schema = json.load(f)
          self.schemas[filename.removesuffix('.json')] = schema

  def find_matching_schema(self, pdf_contnt: str) -> str:
    """
    Find and return the name of the schema that matches the PDF path.
    """
    for schema_name, schema in self.schemas.items():
      if schema.get("identifierRegex"):
        if re.search(schema["identifierRegex"], pdf_contnt):
          return schema_name
    return None