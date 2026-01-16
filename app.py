import streamlit as st
import json
import requests
import time

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL_NAME = "gemini-2.5-flash"

# --- 2. DATABASE MATERI (Sesuai Request) ---
# Data spesifik untuk Kelas 6 Matematika (Bisa ditambah nanti)
DATABASE_MATERI = {
    "6 SD": {
        "Matematika": [
            "Bilangan bulat (positif, negatif, garis bilangan, operasi hitung)",
            "Pecahan (operasi hitung, perkalian, pembagian)",
            "Desimal (operasi hitung, perbandingan)",
            "Lingkaran (jari-jari, diameter, luas, keliling)",
            "Bangun Datar & Ruang (segi banyak, kubus, balok)",
            "Volume (kubus, balok, bangun ruang lainnya)",
            "Pengukuran (satuan, debit, kecepatan, waktu, jarak)",
            "Pengolahan data (daftar, tabel, diagram)",
            "Peluang (kejadian, skala peluang)",
            "Konsep rasio (perbandingan dua besaran)",
            "Rasio bagian ke bagian, bagian ke keseluruhan",
            "Perkenalan notasi aljabar (variabel)"
        ]
    }
}

# --- 3. CSS & FONT CUSTOM (Google Fonts) ---
st.markdown("""
<style>
    /* Import Font Google: Roboto (Title) & Poppins (Subtitle/Body) */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&family=Roboto:wght@700&display=swap');

    /* Title Styling */
    h1 {
        font-family: 'Roboto', sans-serif !important;
        font-weight: 700;
        color: #1F1F1F;
    }
    
    /* Subtitle Styling */
    .subtitle {
        font-family: 'Poppins', sans-serif !important;
        font-size: 18px;
        color: #555555;
        margin-top: -15px;
        margin-bottom: 25px;
    }
    
    /* Tombol */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
    }
    
    /* Expander & Cards */
    div[data-testid="stExpander"] {
        border-radius: 8px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIKA AI (Backend Multi-Soal) ---
def generate_soal_multi(api_key, tipe_soal, data_input, list_kesulitan):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Merangkai Prompt untuk BANYAK soal sekaligus
    req_soal = ""
    for i, level in enumerate(list_kesulitan):
        req_soal += f"- Soal No {i+1}: Tingkat Kesulitan {level}\n"

    # Struktur JSON yang diminta (Array/List)
    if tipe_soal == "Pilihan Ganda":
        json_structure = """
        [
            {
                "no": 1,
                "soal": "Pertanyaan...",
                "opsi": ["A. x", "B. x", "C. x", "D. x"],
                "kunci_index": 0,
                "pembahasan": "..."
            },
            ... (ulangi sesuai jumlah soal)
        ]
        """
    else: # Uraian
        json_structure = """
        [
            {
                "no": 1,
                "soal": "Pertanyaan...",
                "poin_kunci": ["..."],
                "pembahasan": "..."
            }
        ]
        """

    prompt = f"""
    Anda adalah asisten guru profesional Kurikulum Merdeka.
    Buatkan {len(list_kesulitan)} soal {tipe_soal} untuk siswa {data_input['kelas']} SD.
    Mata Pelajaran: {data_input['mapel']}
    Topik Materi: {data_input['topik']}
    
    Detail Permintaan Soal:
    {req_soal}
    
    Output WAJIB berupa JSON Array murni (tanpa markdown):
    {json_structure}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None, f"Error API: {response.text}"
        
        hasil = response.json()
        teks = hasil['candidates'][0]['content']['parts'][0]['text']
        teks_bersih = teks.replace("```json", "").replace("```", "").strip()
        return json.loads(teks_bersih), None
    except Exception as e:
        return None, str(e)

# --- 5. SESSION STATE ---
if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None
if 'tipe_aktif' not in st.session_state:
    st.session_state.tipe_aktif = None

# --- 6. SIDEBAR (PANEL GURU) ---
with st.sidebar:
    st.header("⚙️ Panel Guru")
    
    # API Key Logic
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("🔑 API Key", type="password")

    st.divider()
    
    # 1. Pilih Kelas & Mapel
    kelas = st.selectbox("Kelas", [f"{i} SD" for i in range(1, 7)], index=5) # Default Kelas 6
    mapel = st.selectbox("Mata Pelajaran", ["Matematika", "Bahasa Indonesia", "Bahasa Inggris", "IPA"])
    
    # 2. Logic Topik (Otomatis vs Manual)
    pilihan_topik = []
    topik_final = ""
    
    # Cek apakah ada di database kita?
    if kelas in DATABASE_MATERI and mapel in DATABASE_MATERI[kelas]:
        # Pakai Multiselect (Dropdown Centang)
        st.caption(f"📚 Materi Tersedia ({kelas} - {mapel}):")
        pilihan_topik = st.multiselect(
            "Pilih Sub-Bab / Materi:",
            options=DATABASE_MATERI[kelas][mapel],
            placeholder="Pilih materi (bisa lebih dari 1)"
        )
        # Gabungkan pilihan jadi satu string koma
        if pilihan_topik:
            topik_final = ", ".join(pilihan_topik)
    else:
        # Input Manual jika data belum ada
        topik_final = st.text_input("Topik / Materi", placeholder="Ketik topik materi...")
        if kelas == "6 SD" and mapel == "Matematika":
            pass # Harusnya masuk if atas, ini jaga-jaga
        else:
            st.caption("ℹ️ Database materi untuk kelas ini belum lengkap, silakan ketik manual.")

    st.divider()

    # 3. Jumlah & Kesulitan Soal (Dropdown Dinamis)
    col_jml, col_space = st.columns([1, 0.2])
    with col_jml:
        jml_soal = st.selectbox("Jumlah Soal", [1, 2, 3])
    
    # List untuk menampung level tiap soal
    list_level_request = []
    
    st.caption("Atur Tingkat Kesulitan:")
    # Loop untuk membuat dropdown sesuai jumlah soal
    for i in range(jml_soal):
        lev = st.selectbox(
            f"Soal No. {i+1}", 
            ["Mudah", "Sedang", "Sulit (HOTS)"], 
            key=f"lvl_{i}"
        )
        list_level_request.append(lev)
    
    st.markdown("---")
    if st.button("🗑️ Reset"):
        st.session_state.hasil_soal = None
        st.rerun()

# --- 7. AREA UTAMA (UI BARU) ---

# Header Custom Font
st.markdown("<h1>Generator Soal Sekolah Dasar (SD)</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)

# Tabs
tab_pg, tab_uraian = st.tabs(["📝 Pilihan Ganda", "✍️ Soal Uraian"])

# === TAB PG ===
with tab_pg:
    if st.button("🚀 Generate Soal PG", type="primary"):
        if not api_key:
            st.error("API Key belum diisi.")
        elif not topik_final:
            st.warning("Mohon pilih atau isi Topik Materi terlebih dahulu.")
        else:
            with st.spinner(f"Sedang membuat {jml_soal} soal (Kombinasi: {', '.join(list_level_request)})..."):
                data_input = {"kelas": kelas, "mapel": mapel, "topik": topik_final}
                hasil, error = generate_soal_multi(api_key, "Pilihan Ganda", data_input, list_level_request)
                
                if hasil:
                    st.session_state.hasil_soal = hasil
                    st.session_state.tipe_aktif = "PG"
                else:
                    st.error(error)

    # TAMPILKAN HASIL (Looping)
    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "PG":
        all_soal = st.session_state.hasil_soal
        st.success(f"✅ Berhasil membuat {len(all_soal)} soal tentang: {topik_final}")
        
        # Container Download String
        txt_download = f"LATIHAN SOAL {mapel.upper()} - {kelas}\nMateri: {topik_final}\n\n"
        
        for idx, item in enumerate(all_soal):
            with st.container(border=True):
                # Header Kecil: No 1 (Mudah)
                st.markdown(f"**No. {idx+1}** <span style='color:grey; font-size:0.8em'>({list_level_request[idx]})</span>", unsafe_allow_html=True)
                st.write(item['soal'])
                
                # Radio Button Unik tiap soal
                user_ans = st.radio(f"Jawaban No {idx+1}", item['opsi'], key=f"ans_{idx}")
                
                # Accordion Kunci
                with st.expander("Lihat Kunci & Pembahasan"):
                    kunci_txt = item['opsi'][item['kunci_index']]
                    if user_ans == kunci_txt:
                        st.success(f"Benar! Jawabannya {kunci_txt}")
                    else:
                        st.error(f"Kunci: {kunci_txt}")
                    st.write(f"**Pembahasan:** {item['pembahasan']}")
            
            # Append ke text download
            txt_download += f"{idx+1}. {item['soal']}\n"
            for op in item['opsi']: txt_download += f"   {op}\n"
            txt_download += f"   Kunci: {item['opsi'][item['kunci_index']]}\n   Pembahasan: {item['pembahasan']}\n\n"

        st.download_button("📥 Download Semua Soal (TXT)", txt_download, file_name="Latihan_Soal.txt")

# === TAB URAIAN ===
with tab_uraian:
    if st.button("🚀 Generate Soal Uraian", type="primary"):
        if not api_key or not topik_final:
            st.warning("Lengkapi data dulu.")
        else:
            with st.spinner("Sedang membuat soal uraian..."):
                data_input = {"kelas": kelas, "mapel": mapel, "topik": topik_final}
                hasil, error = generate_soal_multi(api_key, "Uraian", data_input, list_level_request)
                
                if hasil:
                    st.session_state.hasil_soal = hasil
                    st.session_state.tipe_aktif = "URAIAN"
    
    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "URAIAN":
        all_soal = st.session_state.hasil_soal
        txt_download = f"LATIHAN URAIAN {mapel.upper()} - {kelas}\nMateri: {topik_final}\n\n"
        
        for idx, item in enumerate(all_soal):
            with st.container(border=True):
                st.markdown(f"**Soal {idx+1}** <span style='color:grey'>({list_level_request[idx]})</span>", unsafe_allow_html=True)
                st.write(item['soal'])
                st.text_area(f"Jawaban Siswa No {idx+1}", height=100, key=f"essay_{idx}")
                
                with st.expander("Kunci Jawaban Guru"):
                    st.write(item['pembahasan'])
            
            txt_download += f"{idx+1}. {item['soal']}\n   Jawaban: {item['pembahasan']}\n\n"
            
        st.download_button("📥 Download Soal Uraian (TXT)", txt_download, file_name="Soal_Uraian.txt")
