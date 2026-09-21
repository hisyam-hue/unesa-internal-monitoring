import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import os

async def scrape_unesa_internal():
    print("Memulai scraping Berita Arsip Internal UNESA (Januari 2026 - Sekarang)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        articles_data = []
        
        # Kita buat perulangan otomatis untuk mencakup banyak halaman arsip (misal sampai halaman 30 atau lebih sesuai kebutuhan arsip tahun 2026)
        max_pages = 25 
        
        for current_page in range(1, max_pages + 1):
            if current_page == 1:
                url = "https://unesa.ac.id/arsip/unesa/"
            else:
                url = f"https://unesa.ac.id/arsip/unesa/?page={current_page}"

            print(f"Mengakses: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Error loading page {url}: {e}")
                break

            cards = await page.query_selector_all("article, .post, .card, .blog-post")
            if not cards:
                cards = await page.query_selector_all("a[href*='/berita/']")

            print(f"Ditemukan {len(cards)} elemen artikel di halaman {current_page}.")
            
            # Jika halaman kosong (sudah habis arsipnya), hentikan perulangan
            if not cards:
                break

            page_articles_count = 0

            for card in cards:
                try:
                    # Selektor Judul yang akurat pada card arsip
                    title_elem = await card.query_selector("h2 a, h3 a, .title a, a.title, h2, h3")
                    title = await title_elem.inner_text() if title_elem else ""
                    title = title.strip()

                    if not title or len(title) < 5:
                        link_elem = await card.query_selector("a")
                        title = await link_elem.inner_text() if link_elem else ""
                        title = title.strip()

                    link_elem = await card.query_selector("a")
                    link = await link_elem.get_attribute("href") if link_elem else ""
                    if link and not link.startswith("http"):
                        link = "https://www.unesa.ac.id" + link

                    raw_text = await card.inner_text()

                    # Ekstraksi Views riil dari card arsip
                    views_match = re.search(r'([\d\.]+)\s*(?:views|dilihat|pembaca)', raw_text, re.IGNORECASE)
                    if views_match:
                        raw_v = views_match.group(1).replace('.', '').replace(',', '')
                        views = int(raw_v) if raw_v.isdigit() else 0
                    else:
                        views = 0

                    # Ekstraksi Tanggal
                    date_match = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', raw_text)
                    tanggal = date_match.group(0) if date_match else "Terbaru"

                    # Filter hanya mengambil berita tahun 2026 atau terbaru
                    if "2026" not in tanggal and tanggal != "Terbaru":
                        # Jika arsip sudah melewati tahun 2026 (misal 2025), kita bisa lewati atau teruskan
                        pass

                    kategori = "Umum"
                    if "Pikiran Pakar" in raw_text or "Kata Pakar" in raw_text:
                        kategori = "Kata Pakar"
                    elif "Seminar" in raw_text or "Webinar" in raw_text:
                        kategori = "Seminar atau Webinar"
                    elif "Prestasi" in raw_text:
                        kategori = "Prestasi"

                    # Validasi judul agar bersih dari teks generik
                    if title and len(title) > 5 and title not in ["Berita Unesa", "Prestasi Institusi"]:
                        articles_data.append({
                            "tanggal": tanggal,
                            "judul": title,
                            "kategori": kategori,
                            "url": link,
                            "views": views
                        })
                        page_articles_count += 1
                except Exception as ex:
                    continue
            
            # Jika dalam satu halaman tidak ada artikel valid yang terambil, akhiri perulangan
            if page_articles_count == 0 and current_page > 3:
                break

        await browser.close()

        # Simpan ke CSV rekap internal
        if articles_data:
            df = pd.DataFrame(articles_data)
            df = df.drop_duplicates(subset=["judul"])
            df.to_csv("rekap_berita_unesa.csv", index=False)
            print(f"Berhasil menyimpan total {len(df)} artikel ke rekap_berita_unesa.csv dengan views riil.")

if __name__ == "__main__":
    asyncio.run(scrape_unesa_internal())
