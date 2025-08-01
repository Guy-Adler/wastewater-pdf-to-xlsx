#!.venv/bin/python3

from extract import PdfExtractor
from transform import Transformer
from load import Loader
import os

def get_all_example_files():
  """
  Walk through the 'examples' directory and yield all file paths.
  """
  examples_dir = "examples"
  for root, dirs, files in os.walk(examples_dir):
    for file in files:
      if file.endswith('.pdf'):
        yield os.path.join(root, file)


def main():
  for pdf_path in get_all_example_files():
    pdf_extractor = PdfExtractor(pdf_path)
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

    loader = Loader('output.xlsx', 'acre')
    loader.load(transformed_data)

if __name__ == "__main__":
  main()
