import streamlit as st
import json
import requests
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL_NAME = "gemini-2.5-flash"

# --- 2. DATABASE MATERI LENGKAP ---
DATABASE_MATERI = {
    "6 SD": {
        "Matematika": [
            "Bilangan Bulat", "Operasi Hitung Campuran", 
            "Unsur Lingkaran", "Keliling & Luas Lingkaran",
            "Bangun Ruang (Prisma, Tabung, Limas, Kerucut, Bola)",
            "Luas Permukaan & Volume Bangun Ruang",
            "Statistika (Modus, Median, Mean)",
            "Peluang", "Operasi Hitung Pecahan"
        ],
        "IPA": [
            "Perkembangbiakan Tumbuhan & Hewan",
            "Adaptasi Makhluk Hidup",
            "Komponen Listrik & Rangkaian",
            "Sifat-sifat Magnet",
            "Tata Surya", "Rotasi & Revolusi Bumi"
        ],
        "Bahasa Indonesia": [
            "Ide Pokok Paragraf", "Kesimpulan Teks",
            "Teks Eksplanasi", "Teks Pidato",
            "Puisi & Prosa", "Formulir & Daftar Riwayat Hidup"
        ],
        "Bahasa Inggris": [
            "Direction and Location", "Holiday / Past Experience",
            "Government", "Planets / Solar System",
            "Command and Request"
        ]
    }
    # Anda bisa tambahkan kelas lain di sini
}

# --- 3. STYLE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&family=Roboto:wght@700&display=swap');
    
    h1 { font-family: 'Roboto', sans-serif !important; font-weight: 700; color: #1F1F1F; }
    .subtitle { font-family: 'Poppins', sans-serif !important; font-size: 18px; color: #555555; margin-top: -15px; margin-bottom: 25px; }
    
    /* Card Style di Sidebar */
    .config-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #ff4b4b;
    }
    
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-family: 'Poppins', sans-serif; font-weight: 600; }
    .footer-info { font-size: 13px; font-style: italic; color: #666; margin-top: 5px; border-top: 1px dashed #eee; padding-top: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI GENERATE WORD (DOCX) ---
# Sekarang menerima list_request (yang berisi topik & level per soal)
def create_docx(data_soal, tipe, mapel, kelas, list_request):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    # Header Doc
    judul = doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    judul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_paragraph('_' * 70)

    # BAGIAN 1: SOAL
    doc.add_heading('A. SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        # Ambil data topik & level spesifik untuk soal ini
        req_data = list_request[idx]
        topic_txt = req_data['topik']
        level_txt = req_data['level']

        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True
        
        if tipe == "Pilihan Ganda":
            for op in item['opsi']:
                doc.add_paragraph(f"    {op}")
        else:
            doc.add_paragraph("\n" * 3) 

        # Footer Italic Per Soal
        p_footer = doc.add_paragraph(f"Materi: {topic_txt} | Tingkat Kesulitan: {level_txt}")
        p_footer.italic = True
        p_footer.style.font.size = Pt(9)
        p_footer.style.font.color.rgb = RGBColor(100, 100, 100)
        doc.add_paragraph()

    # BAGIAN 2: KUNCI
    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN (Pegangan Guru)', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"No {idx+1}.").bold = True
        
        if tipe == "Pilihan Ganda":
            kunci = item['opsi'][item['kunci_index']]
            p.add_run(f" Jawaban: {kunci}")
        
        doc.add_paragraph(f"Pembahasan: {item['pembahasan']}")
        doc.add_paragraph("-" * 20)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 5. LOGIKA AI ---
def generate_soal_multi_granular(api_key, tipe_soal, kelas, mapel, list_request):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Merakit Prompt Per Soal
    req_str = ""
    for i, req in enumerate(list_request):
        req_str += f"- Soal No {i+1}: Topik '{req['topik']}' dengan Level '{req['level']}'\n"

    if tipe_soal == "Pilihan Ganda":
        json_structure = """[{"no":1,"soal":"...","opsi":["A.","B.","C.","D."],"kunci_index":0,"pembahasan":"..."}]"""
    else:
        json_structure = """[{"no":1,"soal":"...","poin_kunci":["..."],"pembahasan":"..."}]"""

    prompt = f"""
    Buatkan {len(list_request)} soal {tipe_soal} untuk siswa {kelas} SD.
    Mata Pelajaran: {mapel}
    
    Instruksi Spesifik Per Soal:
    {req_str}
    
    Output WAJIB JSON Array:
    {json_structure}
    """
    
    try:
        response = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        if response.status_code != 200: return None, f"Error API: {response.text}"
        
        teks = response.json()['candidates'][0]['content']['parts'][0]['text']
        teks_bersih = teks.replace("```json", "").replace("```", "").strip()
        return json.loads(teks_bersih), None
    except Exception as e: return None, str(e)

# --- 6. SESSION STATE ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'tipe_aktif' not in st.session_state: st.session_state.tipe_aktif = None

# --- 7. SIDEBAR (PANEL GURU) ---
with st.sidebar:
    st.header("⚙️ Panel Guru")
    
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.text_input("🔑 API Key", type="password")

    st.divider()
    
    # Pilih Kelas & Mapel (Global)
    kelas = st.selectbox("Kelas", [f"{i} SD" for i in range(1, 7)], index=5)
    mapel = st.selectbox("Mapel", ["Matematika", "IPA", "Bahasa Indonesia", "Bahasa Inggris"])
    
    st.divider()
    
    # Pilih Jumlah Soal
    jml_soal = st.selectbox("Jumlah Soal:", [1, 2, 3])
    
    # LIST PENAMPUNG REQUEST
    list_request_user = [] 
    
    st.markdown("### 📝 Konfigurasi Per Soal")
    
    # --- LOOPING UNTUK MEMBUAT INPUT PER SOAL ---
    for i in range(jml_soal):
        st.markdown(f"**Soal Nomor {i+1}**")
        
        # 1. Pilih Materi Soal Ini
        # Cek apakah ada materi di database?
        daftar_materi = DATABASE_MATERI.get(kelas, {}).get(mapel, [])
        
        if daftar_materi:
            topik_selected = st.selectbox(
                f"Materi Soal {i+1}", 
                daftar_materi, 
                key=f"topik_{i}"
            )
        else:
            topik_selected = st.text_input(f"Materi Soal {i+1} (Manual)", key=f"topik_{i}")
            
        # 2. Pilih Level Soal Ini
        level_selected = st.selectbox(
            f"Level Soal {i+1}", 
            ["Mudah", "Sedang", "Sulit (HOTS)"], 
            key=f"lvl_{i}"
        )
        
        # Simpan ke list
        list_request_user.append({
            "topik": topik_selected,
            "level": level_selected
        })
        
        st.markdown("---") # Garis pemisah antar soal

    if st.button("🗑️ Reset Konfigurasi"):
        st.session_state.hasil_soal = None
        st.rerun()

# --- 8. UI UTAMA ---
st.markdown("<h1>Generator Soal Sekolah Dasar (SD)</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)

tab_pg, tab_uraian = st.tabs(["📝 Pilihan Ganda", "✍️ Soal Uraian"])

# === TAB PILIHAN GANDA ===
with tab_pg:
    if st.button("🚀 Generate Soal PG", type="primary"):
        if not api_key: st.error("API Key belum diisi")
        else:
            with st.spinner("Sedang meracik soal sesuai pesanan..."):
                res, err = generate_soal_multi_granular(api_key, "Pilihan Ganda", kelas, mapel, list_request_user)
                if res:
                    st.session_state.hasil_soal = res
                    st.session_state.tipe_aktif = "PG"
                else: st.error(err)

    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "PG":
        data = st.session_state.hasil_soal
        
        # Download Button
        docx = create_docx(data, "Pilihan Ganda", mapel, kelas, list_request_user)
        st.download_button("📥 Download Word (.docx)", docx, file_name=f"Soal_PG_{mapel}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        for idx, item in enumerate(data):
            # Ambil info request untuk footer
            info_req = list_request_user[idx]
            
            with st.container(border=True):
                st.write(f"**{idx+1}. {item['soal']}**")
                ans = st.radio(f"Jawab {idx+1}", item['opsi'], key=f"rad_{idx}")
                
                # Footer Italic Sesuai Request
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                
                with st.expander("Kunci Jawaban"):
                    kunci = item['opsi'][item['kunci_index']]
                    if ans == kunci: st.success("Benar!")
                    else: st.error(f"Kunci: {kunci}")
                    st.write(f"**Pembahasan:** {item['pembahasan']}")

# === TAB URAIAN ===
with tab_uraian:
    if st.button("🚀 Generate Soal Uraian", type="primary"):
        if not api_key: st.error("API Key kosong")
        else:
            with st.spinner("Sedang membuat soal uraian..."):
                res, err = generate_soal_multi_granular(api_key, "Uraian", kelas, mapel, list_request_user)
                if res:
                    st.session_state.hasil_soal = res
                    st.session_state.tipe_aktif = "URAIAN"
    
    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "URAIAN":
        data = st.session_state.hasil_soal
        
        docx = create_docx(data, "Uraian", mapel, kelas, list_request_user)
        st.download_button("📥 Download Word (.docx)", docx, file_name=f"Soal_Uraian_{mapel}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        for idx, item in enumerate(data):
            info_req = list_request_user[idx]
            
            with st.container(border=True):
                st.write(f"**Soal {idx+1}:** {item['soal']}")
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                
                st.text_area("Jawab:", height=80, key=f"essay_{idx}")
                with st.expander("Lihat Kunci Guru"):
                    st.write(item['pembahasan'])
