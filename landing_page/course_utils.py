def extract_course_name_and_date(folder=None):
    import os
    if folder is None:
        folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("📂 Searching in folder:", folder)

    for filename in os.listdir(folder):
        print("🔎 Found file:", filename)
        if "Callaway scoring sheet" in filename and filename.endswith(".xls"):
            print("✅ Filename matched:", filename)
            parts = filename.split()
            print("🔍 Filename parts:", parts)

            if len(parts) >= 5:
                course_name = " ".join(parts[:-5])
                month = parts[-5]
                year = parts[-4]
                course_date = f"{month} {year}"
                print(f"🎯 Extracted course name: {course_name}")
                print(f"🗓️ Extracted course date: {course_date}")
                return course_name, course_date
            else:
                print("⚠️ Filename too short to extract course name and date.")
                return "Unknown Course", "Unknown Date"

    print("❌ No matching Callaway scoring sheet file found.")
    return "Unknown Course", "Unknown Date"
