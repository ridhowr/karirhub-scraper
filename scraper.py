import time
import os
import json
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import sync_playwright

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
# SCRAPER
# =========================
def scrape_karirhub():
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Open website...")
        page.goto("https://karirhub.kemnaker.go.id/lowongan-dalam-negeri/lowongan", timeout=60000)

        page.wait_for_selector('a[href*="/lowongan-dalam-negeri/lowongan/"]')

        # scroll load more
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            time.sleep(2)

        print("🔍 Scraping data...")

        cards = page.query_selector_all('a[href*="/lowongan-dalam-negeri/lowongan/"]')

        for card in cards:
            try:
                parent = card.evaluate_handle("el => el.closest('div.text-card-foreground')")

                title = card.inner_text().strip()
                link = "https://karirhub.kemnaker.go.id" + card.get_attribute("href")

                company_el = parent.query_selector("p")
                company = company_el.inner_text() if company_el else ""

                location_el = parent.query_selector(".text-gray-500")
                location = location_el.inner_text() if location_el else ""

                salary = ""
                for d in parent.query_selector_all("div"):
                    txt = d.inner_text()
                    if "Rp" in txt or "Dirahasiakan" in txt:
                        salary = txt
                        break

                deadline = ""
                full_text = parent.inner_text()
                if "Lamar sebelum" in full_text:
                    deadline = full_text.split("Lamar sebelum")[-1].split("\n")[0].strip()

                img = parent.query_selector("img")
                image = img.get_attribute("src") if img else ""

                data.append([
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
                print("Error:", e)

        browser.close()

    return data


# =========================
# UPLOAD TO SHEETS
# =========================
def upload_to_sheets(data):
    sheet = connect_sheet()

    print("📤 Uploading to Google Sheets...")

    for row in data:
        sheet.append_row(row)

    print(f"✅ Done: {len(data)} rows uploaded")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    jobs = scrape_karirhub()
    upload_to_sheets(jobs)