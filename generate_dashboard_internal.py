import pandas as pd
import json
import shutil
import os

def generate_dashboard():
    csv_file = 'rekap_berita_unesa.csv'
    
    if not os.path.exists(csv_file):
        print(f"File {csv_file} tidak ditemukan!")
        return

    # 1. Load Data
    df = pd.read_csv(csv_file)
    df.fillna('', inplace=True)

    total_berita = len(df)
    
    # Ambil kolom tanggal jika ada, atau buat fallback
    col_tanggal = 'tanggal' if 'tanggal' in df.columns else df.columns[0]
    col_judul = 'judul' if 'judul' in df.columns else df.columns[1]
    col_kategori = 'kategori' if 'kategori' in df.columns else 'Kategori'

    # Ringkasan Kategori
    if col_kategori in df.columns:
        kategori_counts = df[col_kategori].value_counts().to_dict()
    else:
        kategori_counts = {'Umum': total_berita}

    # Data untuk Grafik Kategori
    kat_labels = json.dumps(list(kategori_counts.keys()))
    kat_values = json.dumps(list(kategori_counts.values()))

    # 2. Template HTML Interaktif (Sama dengan Standar Eksternal)
    html_template = f"""<!DOCTYPE html>
<html lang="id" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Monitoring Berita Internal UNESA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            50: '#eff6ff',
                            500: '#3b82f6',
                            600: '#2563eb',
                            900: '#1e3a8a',
                        }}
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans antialiased">

    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <div class="p-2 bg-blue-600 rounded-lg text-white">
                    <i class="fa-solid me-1 fa-newspaper text-xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold text-white">Monitoring Berita Internal UNESA</h1>
                    <p class="text-xs text-slate-400">Pembaruan Otomatis Data Website Resmi</p>
                </div>
            </div>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span class="w-2 h-2 mr-2 bg-emerald-400 rounded-full animate-pulse"></span> Sistem Aktif
            </span>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        <!-- Stat Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 backdrop-blur">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-slate-400">Total Publikasi Berita</p>
                        <h3 class="text-3xl font-extrabold text-white mt-2">{total_berita}</h3>
                    </div>
                    <div class="p-3 bg-blue-500/10 text-blue-400 rounded-xl">
                        <i class="fa-solid fa-file-lines text-2xl"></i>
                    </div>
                </div>
            </div>

            <div class="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 backdrop-blur">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-slate-400">Total Kategori</p>
                        <h3 class="text-3xl font-extrabold text-emerald-400 mt-2">{len(kategori_counts)}</h3>
                    </div>
                    <div class="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
                        <i class="fa-solid fa-layer-group text-2xl"></i>
                    </div>
                </div>
            </div>

            <div class="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 backdrop-blur">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-slate-400">Sumber Data</p>
                        <h3 class="text-xl font-bold text-indigo-400 mt-2">unesa.ac.id</h3>
                    </div>
                    <div class="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl">
                        <i class="fa-solid fa-globe text-2xl"></i>
                    </div>
                </div>
            </div>
        </div>

        <!-- Chart Section -->
        <div class="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 backdrop-blur">
            <h2 class="text-lg font-bold text-white mb-4"><i class="fa-solid fa-chart-pie mr-2 text-blue-400"></i>Distribusional Kategori Berita</h2>
            <div class="h-64">
                <canvas id="kategoriChart"></canvas>
            </div>
        </div>

        <!-- News Table -->
        <div class="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 backdrop-blur">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-lg font-bold text-white"><i class="fa-solid fa-list mr-2 text-blue-400"></i>Daftar Berita Terbaru Internal</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-900/80 text-slate-200 uppercase text-xs">
                        <tr>
                            <th class="px-4 py-3 rounded-l-lg">Tanggal</th>
                            <th class="px-4 py-3">Judul Berita</th>
                            <th class="px-4 py-3 rounded-r-lg">Kategori</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-700/50">
"""

    # Populate Rows
    for idx, row in df.iterrows():
        tgl = str(row.get(col_tanggal, '-'))
        jdl = str(row.get(col_judul, '-'))
        kat = str(row.get(col_kategori, 'Umum')) if col_kategori in df.columns else 'Umum'
        
        html_template += f"""
                        <tr class="hover:bg-slate-700/30 transition-colors">
                            <td class="px-4 py-3 whitespace-nowrap text-slate-400">{tgl}</td>
                            <td class="px-4 py-3 font-semibold text-slate-100">{jdl}</td>
                            <td class="px-4 py-3 whitespace-nowrap"><span class="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-1 rounded-full text-xs">{kat}</span></td>
                        </tr>"""

    html_template += f"""
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <script>
        const ctx = document.getElementById('kategoriChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {kat_labels},
                datasets: [{{
                    label: 'Jumlah Berita',
                    data: {kat_values},
                    backgroundColor: '#3b82f6',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: '#334155' }},
                        ticks: {{ color: '#94a3b8' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # Save HTML
    output_html = 'dashboard_internal.html'
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    shutil.copy(output_html, 'index.html')
    print("Dashboard internal & index.html berhasil diperbarui dengan tampilan interaktif!")

if __name__ == '__main__':
    generate_dashboard()
