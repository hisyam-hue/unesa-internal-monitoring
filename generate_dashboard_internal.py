import pandas as pd
import json
import shutil

# 1. Baca data CSV internal
df = pd.read_csv('rekap_berita_unesa.csv')

# 2. Hitung statistik dasar
total_berita = len(df)

# 3. Buat HTML Dashboard Sederhana
html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Berita Internal UNESA</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white p-8">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-3xl font-bold mb-2">Monitoring Berita Internal UNESA</h1>
        <p class="text-slate-400 mb-8">Pembaruan Otomatis Data Website Resmi UNESA</p>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <p class="text-slate-400 text-sm">Total Publikasi Internal</p>
                <h2 class="text-4xl font-bold text-blue-400 mt-2">{total_berita}</h2>
            </div>
        </div>

        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h3 class="text-xl font-bold mb-4">Daftar Berita Terbaru</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-700 text-slate-200">
                        <tr>
                            <th class="p-3">Tanggal</th>
                            <th class="p-3">Judul Berita</th>
                            <th class="p-3">Kategori</th>
                        </tr>
                    </thead>
                    <tbody>
"""

# Tambahkan 10 baris berita terbaru ke tabel
for idx, row in df.head(10).iterrows():
    tgl = row.get('tanggal', '-')
    jdl = row.get('judul', '-')
    kat = row.get('kategori', 'Umum')
    html_content += f"""
                        <tr class="border-b border-slate-700">
                            <td class="p-3">{tgl}</td>
                            <td class="p-3 font-semibold text-white">{jdl}</td>
                            <td class="p-3"><span class="bg-blue-900 text-blue-200 px-2 py-1 rounded text-xs">{kat}</span></td>
                        </tr>"""

html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Simpan ke dashboard_internal.html dan salin ke index.html
with open('dashboard_internal.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

shutil.copy('dashboard_internal.html', 'index.html')
print("Dashboard internal & index.html berhasil dibuat!")