
import os
import sys
from datetime import datetime
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

def archive_scores(course_name, date_played):
    print("Starting archive for:", course_name, date_played)

    conn = get_connection()
    cursor_meta = conn.cursor(buffered=True)
    cursor_archive = conn.cursor(buffered=False)

    try:
        # Step 1: Get course_id
        cursor_meta.execute("SELECT course_id FROM courses WHERE course_name = %s", (course_name,))
        row = cursor_meta.fetchone()
        print("Step 1: course_id fetched")

        if not row:
            print("ERROR: Course not found")
            return

        course_id = row[0]
        print("Step 2: course_id resolved:", course_id)

        # Step 2: Get scores
        cursor_meta.execute("SELECT first_name, last_name, total, net_score FROM scores WHERE course_id = %s", (course_id,))
        scores = cursor_meta.fetchall()
        print(f"Step 3: Retrieved {len(scores)} scores")

        # Step 3: Insert or update snapshot row
        cursor_meta.execute(
            "INSERT INTO course_snapshot (course_id, course_name, date_played) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE course_name = VALUES(course_name)",
            (course_id, course_name, date_played)
        )
        print("Step 4: Snapshot inserted or updated")

        # Get snapshot_id
        cursor_meta.execute(
            "SELECT snapshot_id FROM course_snapshot WHERE course_id = %s AND date_played = %s",
            (course_id, date_played)
        )
        snapshot_id_row = cursor_meta.fetchone()
        if not snapshot_id_row:
            raise Exception("Snapshot row not found after insert.")
        snapshot_id = snapshot_id_row[0]

        # Step 5: Prepare rows for archive
        now = datetime.now()
        rows_to_insert = [
            (
                course_id,
                row[0],  # first_name
                row[1],  # last_name
                row[2],  # total
                row[3],  # net_score
                now,
                snapshot_id
            )
            for row in scores
        ]

        insert_sql = (
            "INSERT INTO scores_archive "
            "(course_id, first_name, last_name, total, net_score, archived_at, snapshot_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )

        if rows_to_insert:
            cursor_archive.executemany(insert_sql, rows_to_insert)
            print(f"Step 5: Archived {len(rows_to_insert)} scores")
        else:
            print("Step 5: No scores to archive")

        conn.commit()
        print("Step 6: Commit complete")

    except mysql.connector.Error as err:
        print("MySQL ERROR:", err)
    finally:
        cursor_archive.close()
        cursor_meta.close()
        conn.close()
        print("Step 7: Connection closed")

def run_from_args():
    if len(sys.argv) != 3:
        print("Usage: python archive_scores_snapshot.py <course_name> <date_played: YYYY-MM-DD>")
        sys.exit(1)

    course_name = sys.argv[1]
    try:
        parsed_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    except ValueError:
        print("ERROR: Invalid date format. Use YYYY-MM-DD.")
        sys.exit(1)

    archive_scores(course_name, parsed_date)

if __name__ == "__main__":
    run_from_args()
