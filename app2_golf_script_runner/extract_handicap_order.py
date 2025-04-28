import pandas as pd
import os

# Use the project root directory
root_dir = "C:\\Golf Web App"
CSV_FILE_PATH = os.path.join(root_dir, "golf_scores.csv")

# Load CSV into a DataFrame
df = pd.read_csv(CSV_FILE_PATH)
df.columns = df.columns.str.strip()

# Debug: Print column names to verify
print("Columns in CSV:", df.columns.tolist())

# Fix typo in column if it exists
df.columns = df.columns.str.replace("6_hanidcap", "6_handicap")

# Extract handicap columns while maintaining CSV order (starting at column 3)
hole_columns = [col for col in df.columns[2:] if "_handicap" in col]

# Debug: Print extracted handicap columns
print("Extracted Handicap Columns:", hole_columns)

# Create a dictionary associating handicap ranking with holes
handicap_to_hole = {rank: hole for rank, hole in enumerate(hole_columns, start=1)}

# Debug: Print the dictionary mapping
print("Handicap to Hole Mapping:", handicap_to_hole)

# Convert dictionary to DataFrame for visualization
handicap_df = pd.DataFrame(list(handicap_to_hole.items()), columns=["Handicap Rank", "Hole Number"])

# Debug: Print the final DataFrame before saving
print("Final Handicap DataFrame:")
print(handicap_df)

# Save to CSV for verification
output_path = os.path.join(root_dir, "handicap_hole_association.csv")
handicap_df.to_csv(output_path, index=False)
