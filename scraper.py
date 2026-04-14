import requests
import time
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# GOOGLE SHEETS CONNECT
# =========================
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)

    sheet = client.open_by_key(
        "170IS8O3Yyj6y1zFhLbD7s9JssVvn2Z5LPm_yE6vZOMw"
    ).worksheet("Sheet1")

    return sheet


# =========================
# FETCH API DATA
# =========================
def fetch_jobs():
    url = "https://karirhub.kemnaker.go.id/api/lowongan?limit=50&page=1"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    print("🌐 Fetching API data...")

    res = requests.get(url, headers=headers, timeout=30)

    if res.status_code != 200:
        print("❌ Failed API:", res.status_code)
        print(res.text[:300])
        return []

    data_json = res.json()

    jobs = []

    # struktur API bisa beda → kita handle fleksibel
    items = data_json.get("data", data_json.get("results", []))

    for item in items:
        try:
            title = item.get("title", "")
            company = item.get("company_name", "")
            location = item.get("location", "")
            link = "https://karirhub.kemnaker.go.id/lowongan/" + item.get("id", "")
            salary = item.get("salary", "")
            deadline = item.get("expiry_date", "")
            image = item.get("company_logo", "")

            jobs.append([
                title,
                company,
                location,
                link,
                salary,
                deadline,
                "",
                "",
                image,
                "",
                ""
            ])

        except Exception as e:
            print("❌ Error item:", e)

    return jobs


# =========================
# UPLOAD TO SHEETS
# =========================
def upload_to_sheets(data):
    if not data:
        print("⚠️ No data found")
        return

    sheet = connect_sheet()

    print(f"📤 Uploading {len(data)} rows...")

    for row in data:
        sheet.append_row(row)

    print("✅ DONE")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("🚀 API SCRAPER START")

    jobs = fetch_jobs()

    print(f"📊 Total: {len(jobs)}")

    upload_to_sheets(jobs)

    print("🎉 FINISH")
