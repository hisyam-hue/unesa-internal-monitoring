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

    async def get_real_views(context, url):
        """Fungsi pembantu untuk masuk ke halaman detail berita dan mengambil views asli"""
        if not url:
            return 0
        page_detail = None
        try:
            page_detail = await context.new_page()
            await page_detail.goto(url, timeout=30000, wait_until="networkidle")
            
            # Berikan jeda waktu 2 detik agar skrip dinamis/counter views selesai merender angka
            await page_detail.wait_for_timeout(2000)
            
            # Ambil seluruh teks bersih dari halaman
            detail_text = await page_detail.inner_text("body")
            
            # Mencari pola angka views yang mengikuti format situs UNESA (contoh: "2.753 views")[cite: 9]
            views_match = re.search(r'([\d\.]+)\s*views', detail_text, re.IGNORECASE)
            if views_match:
                raw_v = views_match.group(1).replace('.', '').replace(',', '')
                if raw_v.isdigit():
                    val = int(raw_v)
                    print(f"Berhasil mendeteksi views untuk {url}: {val}")
                    return val
            
            return 0
        except Exception as e:
            print(f"Gagal akses detail {url}: {e}")
            return 0
        finally:
            if page_detail:
                try:
                    await page_detail.close()
                except:
                    pass

    async with async_playwright() as p:
        # Launch browser headless mode untuk GitHub Actions & Local
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
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

            for card in cards:
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

                    # Ekstraksi Teks Mentah untuk Tanggal & Kategori dari halaman arsip
                    raw_text = await card.inner_text()

                    # Extract Tanggal (sederhana)
                    date_match = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', raw_text)
                    tanggal = date_match.group(0) if date_match else "Terbaru"

                    # Extract Kategori dari Teks Card
                    kategori = "Umum"
                    if "Pikiran Pakar" in raw_text or "Kata Pakar" in raw_text:
                        kategori = "Kata Pakar"
                    elif "Seminar" in raw_text or "Webinar" in raw_text:
                        kategori = "Seminar atau Webinar"

                    # AMBIL VIEWS REAL DARI HALAMAN DETAIL BERITA
                    views = 0
                    if link:
                        views = await get_real_views(context, link)

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
            print("Berhasil menyimpan data rekap_berita_unesa.csv dengan views riil.")

if __name__ == "__main__":
    asyncio.run(scrape_unesa_internal())
