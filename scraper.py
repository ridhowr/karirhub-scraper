import time
from playwright.sync_api import sync_playwright

def scrape_karirhub():
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # WAJIB TRUE di GitHub Actions
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        page = browser.new_page()

        url = "https://karirhub.kemnaker.go.id/lowongan-dalam-negeri/lowongan"

        print("🌐 Membuka website...")
        page.goto(url, timeout=60000)

        # FIX: jangan langsung wait selector (sering timeout)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(10)  # kasih waktu render JS

        print("🔍 Mengambil data...")

        # ambil langsung card container (lebih stabil)
        cards = page.query_selector_all("div.text-card-foreground")

        print(f"📦 Total cards ditemukan: {len(cards)}")

        for card in cards:
            try:
                # TITLE + LINK
                title_el = card.query_selector("h4 a")
                title = title_el.inner_text().strip() if title_el else "-"
                link = "https://karirhub.kemnaker.go.id" + title_el.get_attribute("href") if title_el else "-"

                # COMPANY
                company_el = card.query_selector("p.font-normal")
                company = company_el.inner_text().strip() if company_el else "-"

                # LOCATION
                location_el = card.query_selector(".text-gray-500")
                location = location_el.inner_text().strip() if location_el else "-"

                # SALARY
                salary = "-"
                for d in card.query_selector_all("div"):
                    txt = d.inner_text()
                    if "Rp" in txt or "Dirahasiakan" in txt:
                        salary = txt
                        break

                # DEADLINE
                full_text = card.inner_text()
                deadline = "-"
                if "Lamar sebelum" in full_text:
                    deadline = full_text.split("Lamar sebelum")[-1].split("\n")[0].strip()

                # IMAGE
                img_el = card.query_selector("img")
                image = img_el.get_attribute("src") if img_el else "-"

                data.append({
                    "Title": title,
                    "Company": company,
                    "Location": location,
                    "Link": link,
                    "Salary": salary,
                    "Deadline": deadline,
                    "Level": "-",
                    "Employment Type": "-",
                    "Image URL": image,
                    "Alumni": "-",
                    "Alumni Photo Profile": "-"
                })

            except Exception as e:
                print("❌ Error card:", e)

        browser.close()

    return data


def save_to_excel(data):
    import pandas as pd

    df = pd.DataFrame(data)
    df.to_excel("karirhub_jobs.xlsx", index=False)

    print(f"✅ Berhasil simpan {len(data)} data")


if __name__ == "__main__":
    jobs = scrape_karirhub()
    save_to_excel(jobs)
