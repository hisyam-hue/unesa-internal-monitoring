import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import os

async def scrape_unesa_internal():
    print("Memulai scraping Berita Internal UNESA...")

    # Daftar halaman yang ditarik secara otomatis untuk menjangkau arsip berita lama
    urls = [
        "https://www.unesa.ac.id/kategori/berita",
        "https://www.unesa.ac.id/kategori/berita?page=2",
        "https://www.unesa.ac.id/kategori/berita?page=3"
    ]

    async with async_playwright() as p:
        # Launch browser headless mode untuk GitHub Actions & Local
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_context() # Atau context.new_page() sesuai aslinya
        
        # Menggunakan page dari konteks yang ada
        page = await context.new_page()

        articles_data = []

        for url in urls:
            print(f"Mengakses: {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"Error loading page {url}: {e}")
                continue

            # Selektor artikel berita UNESA
            cards = await page.query_selector_all("article, .post, .card, .blog-post")
            if not cards:
                cards = await page.query_selector_all("a[href*='/berita/']")

            print(f"Ditemukan {len(cards)} elemen artikel di halaman ini.")

            for card in cards[:150]: # Kapasitas batch diperbesar agar berita populer terekam
                try:
                    # Ekstraksi Judul
                    title_elem = await card.query_selector("h1, h2, h3, h4, .title, a")
                    title = await title_elem.inner_text() if title_elem else ""
                    title = title.strip()

                    # Ekstraksi Link
                    link_elem = await card.query_selector("a")
                    link = await link_elem.get_attribute("href") if link_elem else ""
                    if link and not link.startswith("http"):
                        link = "https://www.unesa.ac.id" + link

                    # Ekstraksi Teks Mentah untuk Tanggal, Kategori, & Views
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

        # Simpan ke CSV rekap internal
        if articles_data:
            df = pd.DataFrame(articles_data)
            # Hapus duplikat berdasarkan judul jika ada
            df = df.drop_duplicates(subset=["judul"])
            df.to_csv("rekap_berita_unesa.csv", index=False)
            print("Berhasil menyimpan data rekap_berita_unesa.csv")

if __name__ == "__main__":
    asyncio.run(scrape_unesa_internal())
