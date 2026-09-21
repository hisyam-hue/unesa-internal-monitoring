import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import os

async def scrape_unesa_internal():
    print("Memulai scraping Berita Arsip Internal UNESA...")

    urls = [
        "https://unesa.ac.id/arsip/unesa/",
        "https://unesa.ac.id/arsip/unesa/?page=2",
        "https://unesa.ac.id/arsip/unesa/?page=3"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        articles_data = []

        for url in urls:
            print(f"Mengakses: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                # Beri waktu tambahan agar elemen dinamis ter-load sempurna
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Error loading page {url}: {e}")
                continue

            cards = await page.query_selector_all("article, .post, .card, .blog-post")
            if not cards:
                cards = await page.query_selector_all("a[href*='/berita/']")

            print(f"Ditemukan {len(cards)} elemen artikel di halaman ini.")

            for card in cards:
                try:
                    title_elem = await card.query_selector("h1, h2, h3, h4, .title, a")
                    title = await title_elem.inner_text() if title_elem else ""
                    title = title.strip()

                    link_elem = await card.query_selector("a")
                    link = await link_elem.get_attribute("href") if link_elem else ""
                    if link and not link.startswith("http"):
                        link = "https://www.unesa.ac.id" + link

                    raw_text = await card.inner_text()

                    # DEBUGGING: Cetak teks card ke log untuk melihat isi aslinya
                    print(f"DEBUG CARD TEXT: {raw_text[:150]}...")

                    # Ekstraksi Views dengan berbagai kemungkinan pola penulisan
                    views_match = re.search(r'([\d\.]+)\s*(?:views|dilihat|pembaca)', raw_text, re.IGNORECASE)
                    if views_match:
                        raw_v = views_match.group(1).replace('.', '').replace(',', '')
                        views = int(raw_v) if raw_v.isdigit() else 0
                    else:
                        views = 0

                    date_match = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', raw_text)
                    tanggal = date_match.group(0) if date_match else "Terbaru"

                    kategori = "Umum"
                    if "Pikiran Pakar" in raw_text or "Kata Pakar" in raw_text:
                        kategori = "Kata Pakar"
                    elif "Seminar" in raw_text or "Webinar" in raw_text:
                        kategori = "Seminar atau Webinar"
                    elif "Berita Unesa" in raw_text:
                        kategori = "Berita Unesa"

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

        if articles_data:
            df = pd.DataFrame(articles_data)
            df = df.drop_duplicates(subset=["judul"])
            df.to_csv("rekap_berita_unesa.csv", index=False)
            print("Berhasil menyimpan data rekap_berita_unesa.csv")

if __name__ == "__main__":
    asyncio.run(scrape_unesa_internal())
