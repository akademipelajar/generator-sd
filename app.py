import streamlit as st
import json
import requests
from io import BytesIO
from docx import Document # Library untuk bikin file Word
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL_NAME = "gemini-2.5-flash"

# --- 2. DATABASE MATERI ---
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
        ],
        "IPA": ["Sistem Tata Surya", "Rangkaian Listrik", "Adaptasi Makhluk Hidup", "Magnet", "Pubertas"],
        "Bahasa Indonesia": ["Ide Pokok Paragraf", "Teks Eksplanasi", "Formulir", "Pidato"],
        "Bahasa Inggris": ["Simple Past Tense", "Direction & Location", "Holiday", "Government"]
    }
}

# --- 3. CSS & STYLE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&family=Roboto:wght@700&display=swap');
    h1 { font-family: 'Roboto', sans-serif !important; font-weight: 700; color: #1F1F1F; }
    .subtitle { font-family: 'Poppins', sans-serif !important; font-size: 18px; color: #555555; margin-top: -15px; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-family: 'Poppins', sans-serif; font-weight: 600; }
    .footer-info { font-size: 13px; font-style: italic; color: #666; margin-top: -10px; margin-bottom: 15px; border-top: 1px dashed #eee; padding-top: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI GENERATE WORD (DOCX) ---
def create_docx(data_soal, tipe, mapel, kelas, topik, list_level):
    doc = Document()
    
    # Style Dasar
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    # JUDUL DOKUMEN
    judul = doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    judul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f'Kelas: {kelas}\nMateri: {topik}')
    doc.add_paragraph('_' * 70) # Garis pembatas

    # --- BAGIAN 1: SOAL (Tanpa Kunci) ---
    doc.add_heading('A. SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        level_txt = list_level[idx]
        
        # Tulis Soal
        p = doc.add_paragraph()
        runner = p.add_run(f"{idx+1}. {item['soal']}")
        runner.bold = True
        
        if tipe == "Pilihan Ganda":
            # Tulis Opsi
            for op in item['opsi']:
                doc.add_paragraph(f"    {op}")
        else:
            # Space buat jawaban siswa
            doc.add_paragraph("\n" * 3) 

        # Footer Italic (Request Anda)
        p_footer = doc.add_paragraph(f"Tingkat Kesulitan: {level_txt} | Materi: {topik}")
        p_footer.italic = True
        p_footer.style.font.size = Pt(9)
        p_footer.style.font.color.rgb = RGBColor(100, 100, 100) # Abu-abu
        
        doc.add_paragraph() # Spasi antar soal

    # --- BAGIAN 2: KUNCI JAWABAN (Halaman Baru) ---
    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN DAN PEMBAHASAN', level=1)
    doc.add_paragraph('(Pegangan Guru)')
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"No {idx+1}.").bold = True
        
        if tipe == "Pilihan Ganda":
            kunci = item['opsi'][item['kunci_index']]
            p.add_run(f" Jawaban: {kunci}")
        
        doc.add_paragraph(f"Pembahasan: {item['pembahasan']}")
        
        if tipe == "Uraian" and 'poin_kunci' in item:
            doc.add_paragraph("Poin Penilaian:")
            for pt in item['poin_kunci']:
                doc.add_paragraph(f"- {pt}", style='List Bullet')
        
        doc.add_paragraph("-" * 20)

    # Simpan ke Memory (BytesIO)
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 5. LOGIKA AI ---
def generate_soal_multi(api_key, tipe_soal, data_input, list_kesulitan):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    req_soal = ""
    for i, level in enumerate(list_kesulitan):
        req_soal += f"- Soal No {i+1}: Level {level}\n"

    if tipe_soal == "Pilihan Ganda":
        json_structure = """[{"no":1,"soal":"...","opsi":["A.","B.","C.","D."],"kunci_index":0,"pembahasan":"..."}]"""
    else:
        json_structure = """[{"no":1,"soal":"...","poin_kunci":["..."],"pembahasan":"..."}]"""

    prompt = f"""
    Buatkan {len(list_kesulitan)} soal {tipe_soal} {data_input['kelas']} SD.
    Mapel: {data_input['mapel']}, Topik: {data_input['topik']}
    Detail:
    {req_soal}
    Output JSON Array Murni: {json_structure}
    """
    
    try:
        response = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        if response.status_code != 200: return None, f"Error: {response.text}"
        teks = response.json()['candidates'][0]['content']['parts'][0]['text']
        return json.loads(teks.replace("```json", "").replace("```", "").strip()), None
    except Exception as e: return None, str(e)

# --- 6. SESSION STATE ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'tipe_aktif' not in st.session_state: st.session_state.tipe_aktif = None

# --- 7. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Panel Guru")
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.text_input("🔑 API Key", type="password")
    
    st.divider()
    kelas = st.selectbox("Kelas", [f"{i} SD" for i in range(1, 7)], index=5)
    mapel = st.selectbox("Mapel", ["Matematika", "Bahasa Indonesia", "Bahasa Inggris", "IPA"])
    
    pilihan_topik = []
    topik_final = ""
    if kelas in DATABASE_MATERI and mapel in DATABASE_MATERI[kelas]:
        pilihan_topik = st.multiselect("Pilih Materi:", DATABASE_MATERI[kelas][mapel])
        if pilihan_topik: topik_final = ", ".join(pilihan_topik)
    else:
        topik_final = st.text_input("Topik Manual", placeholder="Ketik topik...")

    col_jml, _ = st.columns([1, 0.2])
    with col_jml: jml_soal = st.selectbox("Jml Soal", [1, 2, 3])
    
    list_level = []
    st.caption("Kesulitan:")
    for i in range(jml_soal):
        list_level.append(st.selectbox(f"No. {i+1}", ["Mudah", "Sedang", "Sulit (HOTS)"], key=f"l_{i}"))
    
    if st.button("🗑️ Reset"):
        st.session_state.hasil_soal = None
        st.rerun()

# --- 8. UI UTAMA ---
st.markdown("<h1>Generator Soal Sekolah Dasar (SD)</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)

tab_pg, tab_uraian = st.tabs(["📝 Pilihan Ganda", "✍️ Soal Uraian"])

# === TAB PG ===
with tab_pg:
    if st.button("🚀 Generate PG", type="primary"):
        if api_key and topik_final:
            with st.spinner("Membuat soal..."):
                res, err = generate_soal_multi(api_key, "Pilihan Ganda", {"kelas":kelas, "mapel":mapel, "topik":topik_final}, list_level)
                if res:
                    st.session_state.hasil_soal = res
                    st.session_state.tipe_aktif = "PG"
                else: st.error(err)
        else: st.warning("Lengkapi data!")

    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "PG":
        data = st.session_state.hasil_soal
        
        # Tombol Download Word
        docx_file = create_docx(data, "Pilihan Ganda", mapel, kelas, topik_final, list_level)
        st.download_button("📥 Download Dokumen Word (.docx)", docx_file, 
                           file_name=f"Soal_PG_{mapel}.docx", 
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        for idx, item in enumerate(data):
            with st.container(border=True):
                st.write(f"**{idx+1}. {item['soal']}**")
                ans = st.radio(f"Jawab {idx+1}", item['opsi'], key=f"pg_{idx}")
                
                # Footer Italic
                st.markdown(f"<div class='footer-info'>Tingkat Kesulitan: {list_level[idx]} | Materi: {topik_final}</div>", unsafe_allow_html=True)
                
                with st.expander("Cek Kunci"):
                    if ans == item['opsi'][item['kunci_index']]: st.success("Benar!")
                    else: st.error(f"Kunci: {item['opsi'][item['kunci_index']]}")
                    st.write(f"**Pembahasan:** {item['pembahasan']}")

# === TAB URAIAN ===
with tab_uraian:
    if st.button("🚀 Generate Uraian", type="primary"):
        if api_key and topik_final:
            with st.spinner("Membuat soal..."):
                res, err = generate_soal_multi(api_key, "Uraian", {"kelas":kelas, "mapel":mapel, "topik":topik_final}, list_level)
                if res:
                    st.session_state.hasil_soal = res
                    st.session_state.tipe_aktif = "URAIAN"
    
    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "URAIAN":
        data = st.session_state.hasil_soal
        
        docx_file = create_docx(data, "Uraian", mapel, kelas, topik_final, list_level)
        st.download_button("📥 Download Dokumen Word (.docx)", docx_file, 
                           file_name=f"Soal_Uraian_{mapel}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        for idx, item in enumerate(data):
            with st.container(border=True):
                st.write(f"**Soal {idx+1}:** {item['soal']}")
                
                # Footer Italic
                st.markdown(f"<div class='footer-info'>Tingkat Kesulitan: {list_level[idx]} | Materi: {topik_final}</div>", unsafe_allow_html=True)
                
                st.text_area("Jawab:", height=100, key=f"ur_{idx}")
                with st.expander("Lihat Kunci Guru"):
                    st.write(item['pembahasan'])
