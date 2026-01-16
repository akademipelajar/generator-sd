import streamlit as st
import json
import requests
import time

# --- 1. KONFIGURASI HALAMAN (Wajib Paling Atas) ---
st.set_page_config(
    page_title="SoalGen Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- KONFIGURASI MODEL (HARDCODED) ---
# Kita kunci ke versi ini sesuai request Anda
MODEL_NAME = "gemini-2.5-flash"

# --- 2. CSS CUSTOM (Tampilan Cantik) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIKA AI (Backend) ---
def generate_soal(api_key, tipe_soal, data):
    # Menggunakan MODEL_NAME yang sudah dikunci di atas
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Prompt disesuaikan dengan tipe soal
    if tipe_soal == "Pilihan Ganda":
        prompt_structure = """
        Output WAJIB JSON Murni:
        {
            "soal": "Teks pertanyaan...",
            "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
            "kunci_index": 0,
            "pembahasan": "Penjelasan lengkap..."
        }
        """
    else: # Uraian
        prompt_structure = """
        Output WAJIB JSON Murni:
        {
            "soal": "Teks pertanyaan essay...",
            "poin_kunci": ["Poin 1...", "Poin 2..."],
            "pembahasan": "Contoh jawaban lengkap..."
        }
        """

    prompt = f"""
    Buatkan 1 soal {tipe_soal} untuk SD.
    - Kelas: {data['kelas']}
    - Mapel: {data['mapel']}
    - Topik: {data['topik']}
    - Level: {data['kesulitan']}
    
    {prompt_structure}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None, f"Error API ({response.status_code}): {response.text}"
        
        hasil = response.json()
        # Parsing Text
        try:
            teks = hasil['candidates'][0]['content']['parts'][0]['text']
            teks_bersih = teks.replace("```json", "").replace("```", "").strip()
            return json.loads(teks_bersih), None
        except:
            return None, "Gagal membaca respon AI. Silakan coba lagi."
            
    except Exception as e:
        return None, str(e)

# --- 4. SESSION STATE (Agar Data Tidak Hilang saat Klik) ---
if 'soal_aktif' not in st.session_state:
    st.session_state.soal_aktif = None
if 'tipe_aktif' not in st.session_state:
    st.session_state.tipe_aktif = None

# --- 5. SIDEBAR (Panel Guru) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=50)
    st.title("Panel Guru")
    st.caption(f"Engine: {MODEL_NAME}") # Info kecil saja
    
    # Cek API Key di Secrets
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Server Terhubung")
    else:
        api_key = st.text_input("🔑 Masukkan API Key", type="password")
        st.info("Input manual (Localhost mode)")

    st.divider()
    
    # Form Input
    kelas = st.selectbox("Kelas", [f"{i} SD" for i in range(1, 7)])
    mapel = st.selectbox("Mata Pelajaran", [
        "Matematika", "IPA", "IPS", 
        "Bahasa Indonesia", "Bahasa Inggris", "PPKn"
    ])
    topik = st.text_input("Topik / Bab Materi", "Pecahan")
    
    st.write("Tingkat Kesulitan:")
    kesulitan = st.select_slider("Level", ["Mudah", "Sedang", "HOTS (Sulit)"], label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("🔄 Reset Aplikasi"):
        st.session_state.soal_aktif = None
        st.rerun()

# --- 6. AREA UTAMA (Main Interface) ---
st.title("🎓 Generator Latihan Soal SD")
st.markdown("Buat soal latihan, ulangan, atau remedial otomatis.")

# Menu Tab
tab_pg, tab_uraian = st.tabs(["📝 Pilihan Ganda", "✍️ Soal Uraian (Essay)"])

# === TAB 1: PILIHAN GANDA ===
with tab_pg:
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        generate_btn = st.button("🚀 Buat Soal PG", key="btn_pg", type="primary")
    
    if generate_btn:
        if not topik or not api_key:
            st.warning("⚠️ Mohon lengkapi Topik materi.")
        else:
            with st.spinner("Sedang meracik soal..."):
                soal, error = generate_soal(api_key, "Pilihan Ganda", 
                                          {"kelas": kelas, "mapel": mapel, "topik": topik, "kesulitan": kesulitan})
                if soal:
                    st.session_state.soal_aktif = soal
                    st.session_state.tipe_aktif = "PG"
                else:
                    st.error(f"Gagal: {error}")

    # Tampilan Hasil PG
    if st.session_state.soal_aktif and st.session_state.tipe_aktif == "PG":
        data = st.session_state.soal_aktif
        
        st.divider()
        st.subheader("Pertanyaan:")
        st.markdown(f"#### {data['soal']}")
        
        jawaban = st.radio("Pilih Jawaban:", data['opsi'], key="radio_pg")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 Cek Kunci Jawaban"):
                kunci_teks = data['opsi'][data['kunci_index']]
                if jawaban == kunci_teks:
                    st.success("✅ JAWABAN BENAR!")
                    st.balloons()
                else:
                    st.error(f"❌ SALAH. Jawaban benar: {kunci_teks}")
                
                with st.expander("Lihat Pembahasan", expanded=True):
                    st.info(data['pembahasan'])
        
        with c2:
            # Format teks untuk download
            txt_content = f"""Mata Pelajaran: {mapel} - Kelas {kelas}\nTopik: {topik}\n\nSOAL:\n{data['soal']}\n\nPILIHAN:\n""" + "\n".join(data['opsi']) + f"""\n\nKUNCI JAWABAN: {data['opsi'][data['kunci_index']]}\n\nPEMBAHASAN:\n{data['pembahasan']}"""
            st.download_button("📥 Download Soal (TXT)", txt_content, file_name=f"Soal_PG_{mapel}.txt")

# === TAB 2: URAIAN ===
with tab_uraian:
    if st.button("🚀 Buat Soal Essay", key="btn_essay", type="primary"):
        if not topik or not api_key:
            st.warning("⚠️ Mohon lengkapi Topik materi.")
        else:
            with st.spinner("Sedang menyusun soal cerita..."):
                soal, error = generate_soal(api_key, "Uraian", 
                                          {"kelas": kelas, "mapel": mapel, "topik": topik, "kesulitan": kesulitan})
                if soal:
                    st.session_state.soal_aktif = soal
                    st.session_state.tipe_aktif = "ESSAY"

    # Tampilan Hasil Essay
    if st.session_state.soal_aktif and st.session_state.tipe_aktif == "ESSAY":
        data = st.session_state.soal_aktif
        
        st.divider()
        st.subheader("Pertanyaan Essay:")
        st.markdown(f"#### {data['soal']}")
        
        st.text_area("Lembar Jawab Siswa (Simulasi):", height=100, placeholder="Ketik jawaban di sini...")
        
        with st.expander("🔐 Lihat Kunci Jawaban Guru"):
            st.markdown("**Poin-poin Penilaian:**")
            for p in data.get('poin_kunci', []):
                st.markdown(f"- {p}")
            st.markdown("---")
            st.markdown(f"**Contoh Jawaban Lengkap:**\n{data['pembahasan']}")
            
        txt_content = f"""Mata Pelajaran: {mapel} - Kelas {kelas}\nTopik: {topik}\n\nSOAL ESSAY:\n{data['soal']}\n\nJAWABAN LENGKAP:\n{data['pembahasan']}"""
        st.download_button("📥 Download Soal (TXT)", txt_content, file_name=f"Soal_Essay_{mapel}.txt")
