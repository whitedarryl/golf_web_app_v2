import os
import win32com.client
import pythoncom
import logging

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

EXCEL_PATH = None
_excel_app = None
_workbook = None
class ExcelCache:
    @staticmethod
    def get_excel_path(force_reload=False):
        global EXCEL_PATH
        if EXCEL_PATH and not force_reload:
            return EXCEL_PATH

        root_dir = os.path.dirname(os.path.dirname(__file__))  # Root directory
        print(f"🔍 Searching for workbook in: {root_dir}")

        for file in os.listdir(root_dir):
            print(f"📂 Found file: {file}")
            if file.endswith("Callaway scoring sheet.xls"):
                EXCEL_PATH = os.path.join(root_dir, file)
                print(f"✅ Workbook found: {EXCEL_PATH}")
                break

        if not EXCEL_PATH:
            raise FileNotFoundError("❌ No Callaway scoring sheet file found")

        return EXCEL_PATH

    @staticmethod
    def get_par():
        ws = ExcelCache.get_sheet()
        par = ws.Cells(2, 22).Value
        print(f"📐 Calculated course par from Excel cell V2: {par}")
        return par

    @staticmethod
    def get_workbook(force_reload=False):
        global _workbook, _excel_app
        if _workbook and not force_reload:
            return _workbook

        pythoncom.CoInitialize()

        try:
            path = ExcelCache.get_excel_path()
            print(f"🔄 Loading workbook from: {path}")
            _excel_app = win32com.client.Dispatch("Excel.Application")
            _excel_app.Visible = False
            _workbook = _excel_app.Workbooks.Open(path)
            if _workbook is None:
                raise Exception("Workbook failed to load. The returned object is None.")
            print(f"✅ Workbook loaded successfully: {_workbook.Name}")
        except Exception as e:
            print(f"❌ Failed to load workbook: {e}")
            if _excel_app:
                _excel_app.Quit()
            return None

        return _workbook

    @staticmethod
    def get_sheet():
        workbook = ExcelCache.get_workbook()
        if workbook is None:
            raise Exception("Workbook is not initialized. Please check the file path or initialization.")

        try:
            for sheet in workbook.Sheets:
                if sheet.Name.lower() == "scores":
                    print(f"✅ Loaded worksheet: {sheet.Name}")
                    return sheet
            raise Exception("Sheet 'Scores' not found in the workbook.")
        except Exception as e:
            print(f"❌ Could not load sheet 'Scores': {e}")
            raise Exception("Sheet 'Scores' not found in the workbook.")

    @staticmethod
    def get_total_players(sheet=None):
        if sheet is None:
            wb = ExcelCache.get_workbook()
            if wb is None:
                logger.error("Workbook is not initialized. Please check the file path or initialization.")
                return "Error: Workbook not found or failed to load", 500
            try:
                sheet = wb.Sheets("Scores")  # Access the "Scores" sheet by name
                print(f"✅ Loaded worksheet: {sheet.Name}")
            except Exception as e:
                print(f"❌ Could not load sheet 'Scores': {e}")
                return 0

        print("🧪 Scanning for valid players in Scores! (A4:B159)")
        name_data = sheet.Range("A4:B159").Value  # Updated range
        print(f"🔍 Raw name data: {name_data}")  # Debug log to print the raw data

        count = 0
        for i, row in enumerate(name_data, start=4):  # Start from row 4
            first, last = row
            print(f"🔍 Row {i}: First='{first}', Last='{last}'")  # Debug log for each row

            if first or last:  # Count rows where at least one field is non-empty
                count += 1
                print(f"✅ Counted as player #{count}")
            else:
                print(f"⏭️ Skipped row {i}")

        print(f"🎯 Total valid players found: {count}")
        return count

    @staticmethod
    def get_submitted_player_count():
        wb = ExcelCache.get_workbook()
        if wb is None:
            logger.error("Workbook is not initialized. Please check the file path or initialization.")
            return "Error: Workbook not found or failed to load", 500
        sheet = wb.Sheets("Scores")  # Access the "Scores" sheet by name

        name_data = sheet.Range("A4:B159").Value  # Updated range
        score_data = sheet.Range("D4:U159").Value
        count = 0

        for name_row, score_row in zip(name_data, score_data):
            first, last = name_row
            if isinstance(first, str) and isinstance(last, str) and any(score_row):
                count += 1

        return count

    @staticmethod
    def get_submitted_players(sheet):
        submitted_names = []
        name_data = sheet.Range("A4:B159").Value  # Updated range
        score_data = sheet.Range("D4:U159").Value

        for name_row, score_row in zip(name_data, score_data):
            first, last = name_row
            if isinstance(first, str) and isinstance(last, str) and any(score_row):
                submitted_names.append(f"{first} {last}")

        return submitted_names

    @staticmethod
    def refresh_cache():
        global _workbook, _excel_app
        if _workbook:
            try:
                _workbook.Close(SaveChanges=True)
            except Exception as e:
                print(f"⚠️ Couldn't close workbook (might be dead): {e}")
        _workbook = None
        _excel_app = None

        # ✅ Reload the workbook immediately
        ExcelCache.get_workbook(force_reload=True)
