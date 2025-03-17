import sqlite3
import csv
import os

def create_database(csv_folder):
    conn = sqlite3.connect("translations.db")
    cursor = conn.cursor()

    # Drop old table if it exists (to avoid conflicts)
    cursor.execute("DROP TABLE IF EXISTS translations")

    # Scan CSV files to detect the highest number of 'nX' columns
    max_n = 0
    for file in os.listdir(csv_folder):
        if file.endswith(".csv"):
            file_path = os.path.join(csv_folder, file)
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                if columns:
                    n_columns = sum(1 for col in columns if col.startswith("n"))
                    max_n = max(max_n, n_columns)

    # Create table dynamically based on detected columns
    n_columns = ", ".join([f"n{i} TEXT" for i in range(1, max_n + 1)])
    cursor.execute(f"""
        CREATE TABLE translations (
            {n_columns},
            darija_ar TEXT, eng TEXT
        )
    """)

    # Insert data from all CSV files
    for file in os.listdir(csv_folder):
        if file.endswith(".csv"):
            file_path = os.path.join(csv_folder, file)
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Get the values for all 'nX' columns dynamically
                    n_values = [row.get(f"n{i}", "") for i in range(1, max_n + 1)]
                    darija_ar = row.get("darija_ar", "")
                    eng = row.get("eng", "")

                    # Insert into table
                    placeholders = ", ".join(["?"] * (max_n + 2))  # Adjust placeholders
                    cursor.execute(f"INSERT INTO translations VALUES ({placeholders})", (*n_values, darija_ar, eng))

    conn.commit()
    conn.close()
    print(f"Database created successfully with {max_n} 'nX' columns!")

# Run script to create database
create_database("data")
