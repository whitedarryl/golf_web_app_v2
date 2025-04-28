
import pandas as pd
import os
import glob

def convert_xls_to_csv():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    pattern = os.path.join(root_dir, "*Callaway scoring sheet.xls")
    xls_files = glob.glob(pattern)

    if not xls_files:
        print(f"Error: No .xls file found in directory: {root_dir}")
        return

    input_xls = xls_files[0]
    output_csv = os.path.join(root_dir, "golf_scores.csv")

    xls = pd.ExcelFile(input_xls)

    if "Scores" not in xls.sheet_names:
        print("Error: 'Scores' sheet not found in the Excel file.")
        return

    df = pd.read_excel(xls, sheet_name="Scores", engine='xlrd')
    df.rename(columns={
        "!st Name": "first_name",
        "1st Name": "first_name",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Total": "total",
        "Net Score": "net_score"
    }, inplace=True)

    df.columns = df.columns.str.strip()

    print("Columns found:", df.columns.tolist())
    print("First 10 rows:")
    print(df.head(10))

    df = df.iloc[2:].reset_index(drop=True)

    required_columns = ["first_name", "last_name"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing expected columns: {missing_columns}")
        return

    valid_hole_columns = [str(i) for i in range(1, 19)]
    df = df[[col for col in ["first_name", "last_name", "total", "net_score"] + valid_hole_columns if col in df.columns]]

    for col in valid_hole_columns + ["total", "net_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df = df.dropna(subset=["first_name", "last_name"])
    df.to_csv(output_csv, index=False)
    print("Sanitized columns:", df.columns.tolist())
    print("Sample names:", df[['first_name', 'last_name']].head())

    print(f"Converted {os.path.basename(input_xls)} to {output_csv}")
    print("Data extraction completed successfully.")

if __name__ == "__main__":
    convert_xls_to_csv()
