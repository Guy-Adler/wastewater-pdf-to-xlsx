from extract import PdfExtractor
from transform import Transformer
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
      "tables": pdf_extractor.tables
    }
    transformer = Transformer(pdf_extractor.schemaName, extracted_data)

    print(f"{pdf_path=}; {transformer.sampling_date=}; {transformer.results=}")

if __name__ == "__main__":
  main()
