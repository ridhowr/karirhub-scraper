import time
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import sync_playwright, TimeoutError

# ================= GOOGLE SHEETS =================
def connect_sheet():
    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key("170IS8O3Yyj6y1zFhLbD7s9JssVvn2Z5LPm_yE6vZOMw").worksheet("Sheet1")
    print("✅ Connected to Google Sheet")

    return sheet


# ================= SCRAPER =================
def scrape_karirhub():
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        page = context.new_page()

        print("🌐 Open website...")
        page.goto("https://karirhub.kemnaker.go.id/lowongan-dalam-negeri/lowongan", timeout=60000)

        # WAIT STRATEGY (GABUNGAN)
        try:
            page.wait_for_selector('a[href*="/lowongan-dalam-negeri/lowongan/"]', timeout=15000)
            print("✅ Selector ketemu")
        except TimeoutError:
            print("⚠️ Selector tidak muncul, pakai fallback delay...")
            time.sleep(15)

        # SCROLL NATURAL
        print("📜 Scrolling...")
        for _ in range(8):
            page.mouse.wheel(0, 2000)
            time.sleep(2)

        time.sleep(5)

        cards = page.query_selector_all('a[href*="/lowongan-dalam-negeri/lowongan/"]')
        print(f"📦 Total cards: {len(cards)}")

        # RETRY kalau 0
        if len(cards) == 0:
            print("🔁 Retry load ulang...")
            page.reload()
            time.sleep(10)

            cards = page.query_selector_all('a[href*="/lowongan-dalam-negeri/lowongan/"]')
            print(f"📦 Retry cards: {len(cards)}")

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
                print("❌ Error:", e)

        browser.close()

    print(f"📊 Total scraped: {len(data)}")
    return data


# ================= UPLOAD =================
def upload_to_sheet(data):
    if not data:
        print("❌ No data to upload")
        return

    sheet = connect_sheet()

    print(f"📤 Upload {len(data)} rows...")
    for row in data:
        sheet.append_row(row)

    print("✅ Upload selesai")


# ================= MAIN =================
if __name__ == "__main__":
    jobs = scrape_karirhub()
    upload_to_sheet(jobs)
