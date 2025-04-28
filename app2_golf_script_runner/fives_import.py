import pandas as pd
import os
import sys
import pymysql
import re
import numpy as np  
import codecs
from dotenv import load_dotenv

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def canonicalize_name(first, last):
    first = str(first).strip()
    last = str(last).strip()
    full = f"{first} {last}"
    if full.lower() == "d j patterson":
        return "DJ", last
    if full.lower() == "mike a carroll":
        return "MikeA", last
    if full.lower() == "mike p carroll":
        return "MikeP", last
    return first, last

# Load environment variables
load_dotenv()
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

TABLE_NAME = "fives"

def sanitize_column_name(column_name):
    column_name = column_name.strip().replace(" ", "_").lower()
    column_name = re.sub(r'\W+', '', column_name)  
    return column_name

def import_fives(file_path, sheet_input):
    try:
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names

        matching_sheets = [sheet for sheet in sheets if sheet_input.lower() in sheet.lower()]
        if not matching_sheets:
            print(f"Error: No matching sheet found for '{sheet_input}'.")
            sys.exit(1)

        selected_sheet = matching_sheets[0]
        print(f"Importing data from: {selected_sheet}")

        df = pd.read_excel(file_path, sheet_name=selected_sheet)
        df.columns = [sanitize_column_name(col) for col in df.columns]

    except Exception as e:
        print(f"ERROR while loading data: {e}")
        sys.exit(1)

    try:
        conn = pymysql.connect(**db_config, autocommit=True)
        cursor = conn.cursor()

    except pymysql.Error as e:
        print(f"ERROR while connecting to MySQL: {e}")
        sys.exit(1)

    try:
        if df.shape[1] < 4:
            print("ERROR: The Excel sheet must have at least four columns.")
            sys.exit(1)

        df.columns = [sanitize_column_name(col) for col in df.columns]
        column_names = list(df.columns)

        column_mapping = {
            column_names[0]: "first_name",
            column_names[1]: "last_name",
            column_names[2]: "juniors",
            column_names[3]: "seniors_ladies",
            column_names[4]: "handicap",
            column_names[5]: "front_9",
            column_names[6]: "front_9_net",
            column_names[7]: "back_9",
            column_names[8]: "back_9_net",
            column_names[9]: "total",
            column_names[10]: "total_net"
        }

        df.rename(columns=column_mapping, inplace=True)
        df.fillna(0, inplace=True)

        numeric_columns = ["handicap", "front_9", "front_9_net", "back_9", "back_9_net", "total", "total_net", "juniors", "seniors_ladies"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    except Exception as e:
        print(f"ERROR while processing data: {e}")
        sys.exit(1)

    try:
        for idx, row in df.iterrows():
            first_name, last_name = canonicalize_name(row["first_name"], row["last_name"])
            cursor.execute(
                """
                SELECT SUM(hole_1 + hole_2 + hole_3 + hole_4 + hole_5 + hole_6 + hole_7 + hole_8 + hole_9),
                       SUM(hole_10 + hole_11 + hole_12 + hole_13 + hole_14 + hole_15 + hole_16 + hole_17 + hole_18),
                       SUM(hole_1 + hole_2 + hole_3 + hole_4 + hole_5 + hole_6 + hole_7 + hole_8 + hole_9 +
                           hole_10 + hole_11 + hole_12 + hole_13 + hole_14 + hole_15 + hole_16 + hole_17 + hole_18)
                FROM scores
                WHERE first_name = %s AND last_name = %s
                """,
                (first_name, last_name)
            )
            scores = cursor.fetchone()
            if scores:
                df.at[idx, "front_9"] = float(scores[0]) if scores[0] is not None else 0.0
                df.at[idx, "back_9"] = float(scores[1]) if scores[1] is not None else 0.0
                df.at[idx, "total"] = float(scores[2]) if scores[2] is not None else 0.0

        df["front_9_net"] = df["front_9"].astype(float) - (df["handicap"].astype(float) / 2)
        df["back_9_net"] = df["back_9"].astype(float) - (df["handicap"].astype(float) / 2)
        df["total_net"] = df["total"].astype(float) - df["handicap"].astype(float)

        df = df.dropna(subset=["first_name", "last_name"])
        df = df[df["first_name"].astype(str).str.strip() != ""]
        df = df[df["last_name"].astype(str).str.strip() != ""]

        if df.empty:
            print("No valid rows to insert. Exiting.")
            sys.exit(0)

    except Exception as e:
        print(f"ERROR while computing scores: {e}")
        sys.exit(1)

    try:
        cursor.execute("TRUNCATE TABLE fives")

        insert_query = """
        INSERT INTO fives (first_name, last_name, juniors, seniors_ladies, handicap, front_9, front_9_net, back_9, back_9_net, total, total_net)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for _, row in df.iterrows():
            first_name, last_name = canonicalize_name(row["first_name"], row["last_name"])

            values = tuple(
                None if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', ''] else val
                for val in [first_name, last_name, row["juniors"], row["seniors_ladies"], row["handicap"],
                            row["front_9"], row["front_9_net"], row["back_9"], row["back_9_net"], row["total"], row["total_net"]]
            )

            cursor.execute(insert_query, values)

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\nSUCCESS: Data from {selected_sheet} imported into 'fives' table.")

    except Exception as e:
        print(f"ERROR while inserting data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Course name (Sheet Name) argument is required.")
        sys.exit(1)

    course_name = sys.argv[1].strip()
    root_dir = "C:\\Golf Web App"
    file_path = next(
        (os.path.join(root_dir, f) for f in os.listdir(root_dir) if f.endswith(".xlsx") and "Five" in f),
        None
    )

    if not file_path:
        print("ERROR: No Excel file found matching 'Five'.")
        sys.exit(1)

    import_fives(file_path, course_name)