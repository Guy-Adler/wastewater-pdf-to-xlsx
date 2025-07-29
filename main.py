from extract import PdfExtractor
import os

def get_all_example_files():
  """
  Walk through the 'examples' directory and yield all file paths.
  """
  examples_dir = "examples/bluegen"
  for root, dirs, files in os.walk(examples_dir):
    for file in files:
      if file.endswith('.pdf'):
        yield os.path.join(root, file)


def main():
  for pdf_path in get_all_example_files():
    pdf_extractor = PdfExtractor(pdf_path)
    print(pdf_extractor.tables)

if __name__ == "__main__":
  main()
