from openpyxl import load_workbook

class WorkbookContext:
    def __init__(self, filename):
        self.filename = filename
        self.wb = None

    def __enter__(self):
        self.wb = load_workbook(self.filename)
        return self.wb

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wb.save(self.filename)
        self.wb.close()
