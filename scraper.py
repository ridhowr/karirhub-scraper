import time
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import sync_playwright


# =========================
# DEBUG (WAJIB)
# =========================
print("🚀 VERSION FINAL RUNNING")
print("📂 FILE:", __file__)
print("📁 DIR:", os.getcwd())


# =========================
# CONNECT GOOGLE SHEETS
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
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        page = browser.new_page()

        print("🌐 Open website...")
        page.goto(
            "https://karirhub.kemnaker.go.id/lowongan-dalam-negeri/lowongan",
            timeout=60000
        )

        # 🔥 FIX UTAMA (TANPA wait_for_selector)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        time.sleep(12)

        print("🔍 Scraping...")

        cards = page.query_selector_all("div.text-card-foreground")

        print(f"📦 Total cards: {len(cards)}")

        for card in cards:
            try:
                # TITLE + LINK
                title_el = card.query_selector("h4 a")
                title = title_el.inner_text().strip() if title_el else ""
                link = "https://karirhub.kemnaker.go.id" + title_el.get_attribute("href") if title_el else ""

                # COMPANY
                company_el = card.query_selector("p.font-normal")
                company = company_el.inner_text().strip() if company_el else ""

                # LOCATION
                location_el = card.query_selector(".text-gray-500")
                location = location_el.inner_text().strip() if location_el else ""

                # SALARY
                salary = ""
                for d in card.query_selector_all("div"):
                    txt = d.inner_text()
                    if "Rp" in txt or "Dirahasiakan" in txt:
                        salary = txt
                        break

                # DEADLINE
                deadline = ""
                full_text = card.inner_text()
                if "Lamar sebelum" in full_text:
                    deadline = full_text.split("Lamar sebelum")[-1].split("\n")[0].strip()

                # IMAGE
                img_el = card.query_selector("img")
                image = img_el.get_attribute("src") if img_el else ""

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
                print("❌ Error card:", e)

        browser.close()

    return data


# =========================
# UPLOAD GOOGLE SHEETS
# =========================
def upload_to_sheet(data):
    if not data:
        print("⚠️ No data ditemukan")
        return

    sheet = connect_sheet()

    print(f"📤 Upload {len(data)} rows...")

    for row in data:
        sheet.append_row(row)

    print("✅ Upload selesai")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    jobs = scrape_karirhub()
    print(f"📊 Total scraped: {len(jobs)}")
    upload_to_sheet(jobs)
    print("🎉 DONE")
