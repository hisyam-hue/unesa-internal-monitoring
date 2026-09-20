import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CSV_FILE = "rekap_berita_unesa.csv"

MONTH_MAP = {
    'Januari': 1, 'Jan': 1, 'Februari': 2, 'Feb': 2, 'Maret': 3, 'Mar': 3,
    'April': 4, 'Apr': 4, 'Mei': 5, 'Juni': 6, 'Jun': 6, 'Juli': 7, 'Jul': 7,
    'Agustus': 8, 'Agu': 8, 'Ags': 8, 'September': 9, 'Sep': 9,
    'Oktober': 10, 'Okt': 10, 'November': 11, 'Nov': 11, 'Desember': 12, 'Des': 12
}

EXCLUDE_WORDS = [
    'selayang pandang', 'pimpinan universitas', 'struktur organisasi', 
    'senat akademik', 'biro, lembaga', 'home', 'tentang unesa', 'pendidikan', 
    'pengabdian', 'research', 'layanan', 'kembali ke beranda'
]

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def categorize_topic(judul):
    j_lower = judul.lower()
    if any(k in j_lower for k in ['juara', 'medali', 'prestasi', 'sabet', 'lomba', 'kompetisi', 'penghargaan', 'peringkat']):
        return 'Prestasi & Penghargaan'
    elif any(k in j_lower for k in ['kerjasama', 'kolaborasi', 'mou', 'mou', 'delegasi', 'kunjungan', 'benchmarking', 'kemitraan']):
        return 'Kerjasama & Internasional'
    elif any(k in j_lower for k in ['riset', 'penelitian', 'jurnal', 'inovasi', 'teknologi', 'karya', 'paten', 'guru besar', 'profesor']):
        return 'Riset & Inovasi'
    elif any(k in j_lower for k in ['kkn', 'pengabdian', 'masyarakat', 'umkm', 'desa', 'pelatihan', 'pendampingan', 'bantu']):
        return 'Pengabdian Masyarakat'
    elif any(k in j_lower for k in ['mahasiswa', 'maba', 'ukm', 'ormawa', 'kampus', 'studi', 'wisuda', 'yudisium', 'beasiswa']):
        return 'Kemahasiswaan'
    else:
        return 'Akademik & Umum'

def parse_date(date_str):
    date_str = clean_text(date_str)
    match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3))
        month = MONTH_MAP.get(month_name, None)
        return day, month, year, f"{day} {month_name} {year}"
    return None, None, None, None

def run_local_scraper():
    all_articles = []
    seen_links = set()
    stop_scraping = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = context.new_page()

        p_num = 1
        while not stop_scraping and p_num <= 100:
            target_url = f"https://unesa.ac.id/arsip/unesa/p/{p_num}/" if p_num > 1 else "https://unesa.ac.id/arsip/unesa/"
            print(f"\n--- Memproses Halaman {p_num} ({target_url}) ---")
            
            try:
                response = page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                if response and response.status == 404:
                    print("Halaman 404. Selesai.")
                    break
            except Exception:
                break

            time.sleep(1.5)

            for _ in range(4):
                page.evaluate("window.scrollBy(0, 600);")
                time.sleep(0.3)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            a_tags = soup.find_all('a')
            count_page = 0

            for a in a_tags:
                link = a.get('href', '')
                if not link or '#' in link or 'javascript' in link:
                    continue

                if not link.startswith('http'):
                    link = 'https://unesa.ac.id' + ('/' if not link.startswith('/') else '') + link

                if 'unesa.ac.id' not in link or link in seen_links:
                    continue

                parent = a.find_parent(['div', 'article', 'li'])
                date_text = ""
                if parent:
                    text_all = parent.get_text()
                    dm = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', text_all)
                    if dm:
                        date_text = dm.group(0)

                day, month, year, formatted_date = parse_date(date_text)

                if not formatted_date or not year:
                    continue

                if year < 2026:
                    print(f">> Menemukan berita tahun {year} ({formatted_date}). Perekaman selesai!")
                    stop_scraping = True
                    break

                judul = clean_text(a.get_text())
                if len(judul) < 20 or any(ex in judul.lower() for ex in EXCLUDE_WORDS):
                    continue

                # Kategori otomatis berdasarkan topik judul
                kategori = categorize_topic(judul)

                all_articles.append({
                    'tanggal': formatted_date,
                    'judul': judul,
                    'kategori': kategori,
                    'link': link,
                    'bulan': month,
                    'tahun': year
                })
                seen_links.add(link)
                count_page += 1

            print(f"Halaman {p_num}: {count_page} artikel berita valid terambil.")

            if stop_scraping:
                break

            p_num += 1

        browser.close()

    if all_articles:
        final_df = pd.DataFrame(all_articles)
        final_df = final_df.drop_duplicates(subset=['link'], keep='first')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"\n==========================================")
        print(f"SUKSES TOTAL! {len(final_df)} berita murni tersimpan dengan kategori terpisah di '{CSV_FILE}'.")
        print(f"==========================================")

if __name__ == "__main__":
    run_local_scraper()