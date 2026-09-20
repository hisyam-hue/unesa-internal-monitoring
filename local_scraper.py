import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import os

async def scrape_unesa_internal():
    print("Memulai scraping Berita Internal UNESA...")
    
    url = "https://www.unesa.ac.id/kategori/berita"
    
    async with async_playwright() as p:
        # Launch browser headless mode untuk GitHub Actions & Local
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"Error loading main page: {e}")
            await browser.close()
            return

        articles_data = []
        
        # Selektor artikel berita UNESA
        cards = await page.query_selector_all("article, .post, .card, .blog-post")
        if not cards:
            cards = await page.query_selector_all("a[href*='/berita/']")

        print(f"Ditemukan {len(cards)} elemen artikel di halaman utama.")

        for card in cards[:30]: # Ambil batch berita terbaru
            try:
                # Extraksi Judul
                title_elem = await card.query_selector("h1, h2, h3, h4, .title, a")
                title = await title_elem.inner_text() if title_elem else ""
                title = title.strip()
                
                # Extraksi Link
                link_elem = await card.query_selector("a")
                link = await link_elem.get_attribute("href") if link_elem else ""
                if link and not link.startswith("http"):
                    link = "https://www.unesa.ac.id" + link

                # Extraksi Teks Mentah untuk Tanggal, Kategori, & Views
                raw_text = await card.inner_text()
                
                # Extract Views (misal: 297 views)
                views_match = re.search(r'(\d+)\s*views', raw_text, re.IGNORECASE)
                views = int(views_match.group(1)) if views_match else 0
                
                # Extract Tanggal (sederhana)
                date_match = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', raw_text)
                tanggal = date_match.group(0) if date_match else "Terbaru"

                # Extract Kategori dari Teks Card
                kategori = "Umum"
                if "Pikiran Pakar" in raw_text or "Kata Pakar" in raw_text:
                    kategori = "Kata Pakar"
                elif "Seminar" in raw_text or "Webinar" in raw_text:
                    kategori = "Seminar atau Webinar"

                if title and len(title) > 10:
                    articles_data.append({
                        "tanggal": tanggal,
                        "judul": title,
                        "kategori": kategori,
                        "url": link,
                        "views": views
                    })
            except Exception as ex:
                continue

        await browser.close()

    # Simpan/Perbarui CSV
    csv_file = "rekap_berita_unesa.csv"
    if articles_data:
        new_df = pd.DataFrame(articles_data)
        if os.path.exists(csv_file):
            old_df = pd.read_csv(csv_file)
            combined_df = pd.concat([new_df, old_df]).drop_duplicates(subset=['judul'], keep='first')
            combined_df.to_csv(csv_file, index=False)
            print(f"Berhasil memperbarui {csv_file}. Total data: {len(combined_df)}")
        else:
            new_df.to_csv(csv_file, index=False)
            print(f"File {csv_file} baru berhasil dibuat dengan {len(new_df)} data.")
    else:
        print("Tidak ada data baru yang didapatkan.")

if __name__ == "__main__":
    asyncio.run(scrape_unesa_internal())
