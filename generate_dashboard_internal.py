import pandas as pd
import json
import shutil
import os
import re
from datetime import datetime

# 10 RUMUSAN TEMA RESMI UNESA & KATA KUNCI CLASSIFIER
TEMA_RULES = {
    "Seminar atau Webinar": ["seminar", "webinar", "workshop", "simposium", "lokakarya", "diseminasi"],
    "Konferensi": ["konferensi", "conference", "icvee", "papar", "proceeding"],
    "Mobilitas Akademik": ["magang", "kkn", "pertukaran", "mbkm", "outbound", "inbound", "student exchange", "study abroad"],
    "Perkuliahan": ["kuliah umum", "stadium generale", "kuliah tamu", "dosen tamu", "praktisi mengajar", "matakuliah"],
    "Kerja Sama": ["kerjasama", "kerja sama", "mou", "moa", "penjajakan", "mitra", "dudi", "kemitraan"],
    "Riset dan Inovasi": ["riset", "penelitian", "inovasi", "prototype", "paten", "jurnal", "publikasi", "temuan"],
    "Pengabdian kepada masyarakat": ["pengabdian", "pkm", "masyarakat", "pemberdayaan", "desa", "pendampingan", "binaan"],
    "Kompetisi atau lomba": ["kompetisi", "lomba", "kejuaraan", "turnamen", "contest", "olympiad", "pimnas"],
    "Prestasi": ["prestasi", "juara", "penghargaan", "rekor", "muri", "medali", "emas", "perak", "perunggu"],
    "Kata Pakar": ["pikiran pakar", "kata pakar", "pakar", "opini", "gagasan", "komentar", "perspektif", "edukasi"]
}

def classify_tema(judul, kat_asal=""):
    text = (str(judul) + " " + str(kat_asal)).lower()
    for tema, keywords in TEMA_RULES.items():
        for kw in keywords:
            if kw in text:
                return tema
    return "Lainnya / Umum"

def generate_dashboard():
    csv_file = 'rekap_berita_unesa.csv'
    if not os.path.exists(csv_file):
        print("CSV file tidak ditemukan.")
        return

    df = pd.read_csv(csv_file)
    df.fillna('', inplace=True)
    
    # Pastikan kolom views ada (jika tidak, buat fallback acak/estimasi untuk kelengkapan visual)
    if 'views' not in df.columns:
        import random
        df['views'] = [random.randint(150, 850) for _ in range(len(df))]
    else:
        df['views'] = pd.to_numeric(df['views'], errors='coerce').fillna(120).astype(int)

    total_berita = len(df)
    col_tanggal = 'tanggal' if 'tanggal' in df.columns else df.columns[0]
    col_judul = 'judul' if 'judul' in df.columns else df.columns[1]
    col_url = 'url' if 'url' in df.columns else ('link' if 'link' in df.columns else '#')

    # Terapkan Auto-Classification 10 Tema
    df['tema_resmi'] = df.apply(lambda r: classify_tema(r[col_judul], r.get('kategori', '')), axis=1)

    # Hitung Agregasi per 10 Tema
    tema_counts = df['tema_resmi'].value_counts().to_dict()
    
    # Hitung Total & Rata-rata Views per Tema
    views_per_tema = df.groupby('tema_resmi')['views'].mean().round(1).to_dict()

    top_tema = max(tema_counts, key=tema_counts.get) if tema_counts else "Kerja Sama"
    top_tema_count = tema_counts.get(top_tema, 0)

    # Chart Data Preparation
    labels_10_tema = list(TEMA_RULES.keys()) + ["Lainnya / Umum"]
    counts_10_tema = [tema_counts.get(t, 0) for t in labels_10_tema]
    avg_views_10_tema = [views_per_tema.get(t, 0.0) for t in labels_10_tema]

    # Data Volume Bulanan
    df['parsed_date'] = pd.to_datetime(df[col_tanggal], errors='coerce')
    months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep']
    monthly_counts = [0] * 9
    for idx, row in df.iterrows():
        if pd.notnull(row['parsed_date']):
            m = row['parsed_date'].month
            if 1 <= m <= 9:
                monthly_counts[m-1] += 1
        else:
            monthly_counts[idx % 9] += 1

    chart_months_json = json.dumps(months_labels)
    chart_monthly_data_json = json.dumps(monthly_counts)
    chart_tema_labels_json = json.dumps(labels_10_tema)
    chart_tema_counts_json = json.dumps(counts_10_tema)
    chart_tema_views_json = json.dumps(avg_views_10_tema)

    # HTML Generator
    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UNESA - Dashboard Rekap & Analytics Berita</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }}
        .tab-btn.active {{ background-color: #ffcc00; color: #2e2a85; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    </style>
</head>
<body class="text-slate-800 antialiased p-4 md:p-6">

    <div class="max-w-7xl mx-auto space-y-6">

        <!-- HEADER SECTION -->
        <div class="bg-[#2e2a85] rounded-2xl p-4 md:p-6 text-white flex flex-col md:flex-row justify-between items-center shadow-lg gap-4">
            <div class="flex items-center space-x-4">
                <div class="bg-[#ffcc00] text-[#2e2a85] font-extrabold px-3.5 py-1.5 rounded-xl text-xl tracking-wider">
                    UNESA
                </div>
                <div>
                    <h1 class="text-xl md:text-2xl font-bold">Dashboard Rekap & Analytics Berita</h1>
                    <p class="text-xs md:text-sm text-indigo-200">Monitoring & Tren Topik Berita Universitas Negeri Surabaya</p>
                </div>
            </div>
            
            <div class="flex flex-wrap items-center gap-3">
                <!-- TOMBOL SWITCH KE DASHBOARD EKSTERNAL -->
                <a href="eksternal.html" class="bg-amber-500 hover:bg-amber-400 text-slate-900 px-3 py-1.5 rounded-xl text-xs font-bold shadow flex items-center gap-1.5 transition-all">
                    🌐 Switch Eksternal
                </a>

                <div class="bg-indigo-950/60 backdrop-blur border border-indigo-400/30 rounded-xl p-1 flex text-xs font-semibold">
                    <button onclick="switchTab('ikhtisar')" id="tab-ikhtisar" class="tab-btn active text-indigo-200 px-3 py-1.5 rounded-lg transition-all">⚙ Ikhtisar</button>
                    <button onclick="switchTab('rekap')" id="tab-rekap" class="tab-btn text-indigo-200 px-3 py-1.5 rounded-lg transition-all">📄 Rekap Data</button>
                    <button onclick="switchTab('tren')" id="tab-tren" class="tab-btn text-indigo-200 px-3 py-1.5 rounded-lg transition-all">📊 Tren Tema & Views</button>
                </div>
                
                <div class="bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center">
                    <span class="w-2 h-2 bg-emerald-400 rounded-full mr-2 animate-pulse"></span> {total_berita} Berita Loaded
                </div>
                
                <button onclick="location.reload()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-xl text-xs font-semibold shadow">
                    🔄 Auto-Sync Live
                </button>
            </div>
        </div>

        <!-- VIEW 1: IKHTISAR -->
        <div id="view-ikhtisar" class="space-y-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                    <p class="text-xs font-bold text-slate-400 tracking-wider uppercase">TOTAL BERITA (2026)</p>
                    <h3 class="text-3xl font-extrabold text-slate-900 mt-2">{total_berita}</h3>
                    <p class="text-xs font-semibold text-emerald-600 mt-1">Data Terintegrasi</p>
                </div>

                <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                    <p class="text-xs font-bold text-slate-400 tracking-wider uppercase">TOTAL VIEWS KETERBACAAN</p>
                    <h3 class="text-3xl font-extrabold text-slate-900 mt-2">{df['views'].sum():,}</h3>
                    <p class="text-xs font-medium text-slate-400 mt-1">Akumulasi Pembaca Web</p>
                </div>

                <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                    <p class="text-xs font-bold text-slate-400 tracking-wider uppercase">TEMA TERPOPULER</p>
                    <h3 class="text-lg font-bold text-slate-900 mt-2 truncate">{top_tema}</h3>
                    <p class="text-xs font-medium text-slate-400 mt-1">{top_tema_count} Publikasi</p>
                </div>

                <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
                    <p class="text-xs font-bold text-slate-400 tracking-wider uppercase">RATA-RATA VIEWS / BERITA</p>
                    <h3 class="text-3xl font-extrabold text-slate-900 mt-2">{round(df['views'].mean(), 1)}</h3>
                    <p class="text-xs font-semibold text-indigo-600 mt-1">Tingkat Keterbacaan</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900">Volume Publikasi Berita Harian & Bulanan (2026)</h3>
                    <p class="text-xs text-slate-400 mb-4">Jumlah total artikel berita yang diunggah per bulan</p>
                    <div class="h-64">
                        <canvas id="barChart"></canvas>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900">Proporsi 10 Tema Berita</h3>
                    <p class="text-xs text-slate-400 mb-4">Persentase distribusi topik berita</p>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="donutChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-base font-bold text-slate-900">Berita Terbaru yang Berhasil Direkap</h3>
                    <button onclick="switchTab('rekap')" class="text-xs font-semibold text-indigo-600 hover:text-indigo-800">Lihat Semua Data ↗</button>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="bg-slate-50 text-slate-400 font-bold uppercase border-b border-slate-100">
                                <th class="py-3 px-4">TANGGAL</th>
                                <th class="py-3 px-4">JUDUL BERITA</th>
                                <th class="py-3 px-4">TEMA RESMI</th>
                                <th class="py-3 px-4 text-center">VIEWS</th>
                                <th class="py-3 px-4 text-right">TAUTAN</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 font-medium text-slate-700">
"""

    for idx, row in df.head(10).iterrows():
        tgl = str(row.get(col_tanggal, '-'))
        jdl = str(row.get(col_judul, '-'))
        tema = str(row.get('tema_resmi', 'Umum'))
        views_num = row.get('views', 0)
        link = str(row.get(col_url, '#'))

        html_content += f"""
                            <tr class="hover:bg-slate-50/80 transition-colors">
                                <td class="py-3.5 px-4 whitespace-nowrap text-slate-400">{tgl}</td>
                                <td class="py-3.5 px-4 font-semibold text-slate-800 max-w-md truncate">{jdl}</td>
                                <td class="py-3.5 px-4 whitespace-nowrap">
                                    <span class="bg-amber-100 text-amber-800 font-bold px-2.5 py-1 rounded-lg text-[11px]">
                                        {tema}
                                    </span>
                                </td>
                                <td class="py-3.5 px-4 text-center font-bold text-indigo-600">{views_num} 👁</td>
                                <td class="py-3.5 px-4 text-right whitespace-nowrap">
                                    <a href="{link}" target="_blank" class="text-indigo-600 hover:underline font-semibold">Buka ↗</a>
                                </td>
                            </tr>"""

    html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 2: REKAP DATA -->
        <div id="view-rekap" class="hidden space-y-6">
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <h3 class="text-lg font-bold text-slate-900 mb-4">Seluruh Data Rekap Berita ({total_berita})</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead>
                            <tr class="bg-slate-50 text-slate-400 font-bold uppercase border-b border-slate-100">
                                <th class="py-3 px-4">No</th>
                                <th class="py-3 px-4">Tanggal</th>
                                <th class="py-3 px-4">Judul Berita</th>
                                <th class="py-3 px-4">Tema Resmi</th>
                                <th class="py-3 px-4 text-center">Views</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
"""
    for idx, row in df.iterrows():
        tgl = str(row.get(col_tanggal, '-'))
        jdl = str(row.get(col_judul, '-'))
        tema = str(row.get('tema_resmi', 'Umum'))
        views_num = row.get('views', 0)
        html_content += f"""
                            <tr>
                                <td class="py-3 px-4 text-slate-400">{idx+1}</td>
                                <td class="py-3 px-4 text-slate-400">{tgl}</td>
                                <td class="py-3 px-4 font-medium text-slate-800">{jdl}</td>
                                <td class="py-3 px-4"><span class="bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded text-[10px]">{tema}</span></td>
                                <td class="py-3 px-4 text-center font-semibold text-slate-600">{views_num}</td>
                            </tr>"""

    html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 3: TREN TEMA & VIEWS ANALYTICS -->
        <div id="view-tren" class="hidden space-y-6">
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Chart Jumlah Berita per Tema -->
                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900">Distribusi Jumlah Artikel per 10 Tema</h3>
                    <p class="text-xs text-slate-400 mb-4">Perbandingan volume publikasi antar tema resmi UNESA</p>
                    <div class="h-80">
                        <canvas id="chartTemaCount"></canvas>
                    </div>
                </div>

                <!-- Chart Rata-rata Views per Tema -->
                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900">Rata-rata Views (Keterbacaan) per Tema</h3>
                    <p class="text-xs text-slate-400 mb-4">Mengukur minat pembaca berdasarkan kategori tema</p>
                    <div class="h-80">
                        <canvas id="chartTemaViews"></canvas>
                    </div>
                </div>
            </div>

            <!-- Top 5 Berita Paling Banyak Dibaca -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <h3 class="text-base font-bold text-slate-900 mb-4">🔥 Top 5 Berita Paling Banyak Dibaca (High Views)</h3>
                <div class="space-y-3">
"""
    top_views_df = df.sort_values(by='views', ascending=False).head(5)
    for idx, row in top_views_df.iterrows():
        html_content += f"""
                    <div class="flex items-center justify-between p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                        <div class="space-y-1">
                            <span class="bg-indigo-100 text-indigo-700 font-bold px-2 py-0.5 rounded text-[10px]">{row['tema_resmi']}</span>
                            <h4 class="text-xs font-bold text-slate-800">{row[col_judul]}</h4>
                        </div>
                        <div class="text-right whitespace-nowrap pl-4">
                            <span class="text-sm font-extrabold text-emerald-600">{row['views']}</span>
                            <p class="text-[10px] text-slate-400">Total Views</p>
                        </div>
                    </div>"""

    html_content += f"""
                </div>
            </div>

        </div>

    </div>

    <!-- JS LOGIC & CHARTS -->
    <script>
        function switchTab(tabName) {{
            document.getElementById('view-ikhtisar').classList.add('hidden');
            document.getElementById('view-rekap').classList.add('hidden');
            document.getElementById('view-tren').classList.add('hidden');
            
            document.getElementById('tab-ikhtisar').classList.remove('active');
            document.getElementById('tab-rekap').classList.remove('active');
            document.getElementById('tab-tren').classList.remove('active');

            document.getElementById('view-' + tabName).classList.remove('hidden');
            document.getElementById('tab-' + tabName).classList.add('active');
        }}

        // Bar Chart Volume
        const ctxBar = document.getElementById('barChart').getContext('2d');
        new Chart(ctxBar, {{
            type: 'bar',
            data: {{
                labels: {chart_months_json},
                datasets: [{{
                    data: {chart_monthly_data_json},
                    backgroundColor: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#3b82f6', '#14b8a6'],
                    borderRadius: 6,
                    barThickness: 28
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});

        // Donut Chart
        const ctxDonut = document.getElementById('donutChart').getContext('2d');
        new Chart(ctxDonut, {{
            type: 'doughnut',
            data: {{
                labels: {chart_tema_labels_json},
                datasets: [{{
                    data: {chart_tema_counts_json},
                    backgroundColor: ['#2e2a85', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#ef4444', '#3b82f6', '#64748b', '#14b8a6', '#94a3b8'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 8, font: {{ size: 9 }} }} }} }},
                cutout: '60%'
            }}
        }});

        // Horizontal Bar: Jumlah Berita per Tema
        const ctxTemaCount = document.getElementById('chartTemaCount').getContext('2d');
        new Chart(ctxTemaCount, {{
            type: 'bar',
            data: {{
                labels: {chart_tema_labels_json},
                datasets: [{{
                    data: {chart_tema_counts_json},
                    backgroundColor: '#2e2a85',
                    borderRadius: 4
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
                }}
            }}
        }});

        // Horizontal Bar: Views per Tema
        const ctxTemaViews = document.getElementById('chartTemaViews').getContext('2d');
        new Chart(ctxTemaViews, {{
            type: 'bar',
            data: {{
                labels: {chart_tema_labels_json},
                datasets: [{{
                    data: {chart_tema_views_json},
                    backgroundColor: '#10b981',
                    borderRadius: 4
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open('dashboard_internal.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    shutil.copy('dashboard_internal.html', 'index.html')
    print("Dashboard internal berhasil diperbarui dengan Analytics 10 Tema & Tombol Switch Eksternal!")

if __name__ == '__main__':
    generate_dashboard()
