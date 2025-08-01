"""
Schema utilities for loading data to various excel formats.
"""
import os
import json

class LoadSchemaManager:
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
    Load and return the schemas for transforming to structured data.
    """

    self.schemas = {}
    schemas_dir = "schemas/load"
    for filename in os.listdir(schemas_dir):
      if filename.endswith(".json"):
        with open(os.path.join(schemas_dir, filename), "r", encoding="utf-8") as f:
          schema = json.load(f)
          self.schemas[filename.removesuffix('.json')] = schema

  def get_schema(self, schema_name: str) -> dict:
    """
    Get the schema by name.
    """
    return self.schemas.get(schema_name, None)
