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
                <!-- TOMBOL SWITCH KE DASHBOARD EKSTERNAL (URL GITHUB PAGES) -->
                <a href="https://hisyam-hue.github.io/unesa-external-monitoring/" target="_blank" class="bg-[#ffcc00] hover:bg-yellow-400 text-[#2e2a85] px-3.5 py-2 rounded-xl text-xs font-extrabold shadow-md flex items-center gap-1.5 transition-all">
                    <span>🌐</span> Switch ke Eksternal ↗
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
