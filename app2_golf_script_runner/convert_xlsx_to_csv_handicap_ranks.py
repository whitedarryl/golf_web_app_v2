
import pandas as pd
import os
import glob

def convert_xls_to_handicap_csv():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    pattern = os.path.join(root_dir, "*Callaway scoring sheet.xls")
    xls_files = glob.glob(pattern)

    if not xls_files:
        print(f"Error: No .xls file found in directory: {root_dir}")
        return

    input_xls = xls_files[0]
    output_csv = os.path.join(root_dir, "handicap_ranks.csv")

    xls = pd.ExcelFile(input_xls)

    if "Scores" not in xls.sheet_names:
        print("Error: 'Scores' sheet not found in the Excel file.")
        return

    df = pd.read_excel(xls, sheet_name="Scores", engine='xlrd', header=None)
    handicap_ranks = df.iloc[2, 3:21].tolist()
    handicap_df = pd.DataFrame({"hole_number": range(1, 19), "handicap_rank": handicap_ranks})
    handicap_df.to_csv(output_csv, index=False)

    print(f"Extracted handicap ranks from {os.path.basename(input_xls)} and saved to {output_csv}")

if __name__ == "__main__":
    convert_xls_to_handicap_csv()
