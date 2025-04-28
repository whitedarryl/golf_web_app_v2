
import os
import sys
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

def import_scores(course_id, file_path):
    print(f"Loading file from: {file_path}", flush=True)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    print("Columns found:", df.columns.tolist())

    if "first_name" in df.columns and "last_name" in df.columns:
        print("Name column preview:")
        print(df[['first_name', 'last_name']].head(10))
    else:
        print("Missing 'first_name' or 'last_name' columns!")

    for col in ["total", "net_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    hole_cols = [str(i) for i in range(1, 19)]
    hole_renamed = {col: f"hole_{col}" for col in hole_cols if col in df.columns}

    for col in hole_renamed:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    conn = get_connection()
    cursor = conn.cursor()

    print("Clearing existing scores...")
    cursor.execute("DELETE FROM scores")

    insert_sql = (
        f"INSERT INTO scores (course_id, first_name, last_name, "
        f"{', '.join(hole_renamed.values())}, total, net_score) "
        f"VALUES ({', '.join(['%s'] * (len(hole_renamed) + 5))})"
    )

    rows_inserted = 0
    for idx, row in df.iterrows():
        first = row.get("first_name", "").strip()
        last = row.get("last_name", "").strip()

        if not first or not last:
            print(f"Skipping row {idx+1}: missing name: {row.to_dict()}")
            continue

        values = (
            course_id,
            first,
            last,
            *[row[col] for col in hole_renamed],
            row.get("total", 0),
            row.get("net_score", 0),
        )

        try:
            cursor.execute(insert_sql, values)
            rows_inserted += 1
        except mysql.connector.errors.IntegrityError as e:
            print(f"Skipping duplicate row {idx+1}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Import completed successfully. Total rows inserted: {rows_inserted}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python import_golf_scores.py <course_id> <csv_file_path>")
        sys.exit(1)

    course_id = int(sys.argv[1])
    csv_file_path = sys.argv[2]
    import_scores(course_id, csv_file_path)
