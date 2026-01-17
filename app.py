import streamlit as st
import json
import requests
import os
import time
from io import BytesIO
from urllib.parse import quote
from docx import Document
from docx.shared import Inches
from openai import OpenAI

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD",
    page_icon="📚",
    layout="wide"
)

# --- 2. STYLE CSS (DIKUNCI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');
    .header-title { font-family: 'League Spartan', sans-serif; font-size: 32px; font-weight: bold; line-height: 1.2; color: #1E1E1E; }
    .header-sub { font-family: 'Poppins', sans-serif; font-size: 18px; font-weight: bold; font-style: italic; color: #444; margin-bottom: 5px; }
    .warning-text { font-size: 13px; color: #d9534f; font-weight: bold; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #e6f3ff 0%, #ffffff 100%); border-right: 1px solid #d1e3f3; }
    .metadata-text { font-size: 12px; font-style: italic; font-family: 'Poppins', sans-serif; font-weight: bold; color: #555; margin-top: 10px; }
    div.stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE MATERI ---
DATABASE_MATERI = {
    "1 SD": {"Matematika": ["Bilangan sampai 10", "Penjumlahan & Pengurangan", "Bentuk Bangun Datar"], "IPA": ["Anggota Tubuh"], "Bahasa Indonesia": ["Mengenal Huruf"], "Bahasa Inggris": ["Colors"]},
    "2 SD": {"Matematika": ["Perkalian Dasar", "Pembagian Dasar", "Bangun Datar & Ruang"], "IPA": ["Wujud Benda"], "Bahasa Indonesia": ["Ungkapan Santun"], "Bahasa Inggris": ["Animals"]},
    "3 SD": {"Matematika": ["Pecahan Sederhana", "Simetri & Sudut", "Diagram Gambar"], "IPA": ["Ciri Makhluk Hidup"], "Bahasa Indonesia": ["Dongeng Hewan"], "Bahasa Inggris": ["Telling Time"]},
    "4 SD": {"Matematika": ["Pecahan Senilai", "KPK dan FPB", "Segi Banyak", "Diagram Batang"], "IPA": ["Gaya dan Gerak"], "Bahasa Indonesia": ["Gagasan Pokok"], "Bahasa Inggris": ["Transportation"]},
    "5 SD": {"Matematika": ["Operasi Pecahan", "Kecepatan dan Debit", "Volume Kubus & Balok"], "IPA": ["Organ Pernapasan"], "Bahasa Indonesia": ["Iklan"], "Bahasa Inggris": ["Health Problems"]},
    "6 SD": {"Matematika": ["Bilangan Bulat Negatif", "Lingkaran", "Modus Median Mean"], "IPA": ["Tata Surya"], "Bahasa Indonesia": ["Teks Laporan"], "Bahasa Inggris": ["Simple Past Tense"]}
}

# --- 4. FUNGSI LOGIKA GAMBAR ---
def construct_img_url(prompt):
    full_prompt = f"{prompt}, simple flat 2d educational chart, high contrast, clean white background, no human faces, vector style"
    return f"https://image.pollinations.ai/prompt/{quote(full_prompt)}?width=600&height=400&nologo=true&seed={int(time.time())}"

def safe_download_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200: return BytesIO(resp.content)
    except: return None
    return None

# --- 5. FUNGSI GENERATE WORD ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True
        if item.get('img_url'):
            img_data = safe_download_image(item['img_url'])
            if img_data:
                try: doc.add_picture(img_data, width=Inches(3.5))
                except: pass
        labels = ['A', 'B', 'C', 'D']
        for i, op in enumerate(item['opsi']):
            prefix = f"{labels[i]}. "
            doc.add_paragraph(op if op.startswith(tuple(labels)) else f"{prefix}{op}")
        meta = doc.add_paragraph(f"Materi: {item['materi']} | Level: {item['level']}")
        meta.italic = True
    doc.add_page_break()
    doc.add_heading('KUNCI JAWABAN', level=1)
    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"No {idx+1}: {item['pembahasan']}")
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 6. SESSION STATE & SIDEBAR ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

with st.sidebar:
    suffix = st.session_state.reset_counter
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1]); c2.image("logo.png", width=100)
    
    st.markdown("### ⚙️ Konfigurasi")
    api_key = st.secrets.get("OPENAI_API_KEY") or st.text_input("OpenAI API Key", type="password", key=f"api_{suffix}")
    if not api_key: st.stop()

    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()), key=f"k_{suffix}")
    mapel_sel = st.selectbox("Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()), key=f"m_{suffix}")
    jml_soal = st.slider("Jumlah Soal", 1, 5, 2, key=f"j_{suffix}")

    # LOGIKA PROTEKSI GAMBAR (MAKSIMAL 1)
    req_details = []
    any_img_selected = False
    
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=(i==0)):
            topik = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t_{i}_{suffix}")
            level = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], key=f"l_{i}_{suffix}")
            
            # Jika sudah ada gambar terpilih di soal lain, matikan checkbox ini
            is_disabled = any_img_selected
            label_img = "Gunakan Gambar" if not is_disabled else "Gunakan Gambar (Maksimal 1)"
            
            img_on = st.checkbox(label_img, value=False, key=f"img_{i}_{suffix}", disabled=is_disabled)
            if img_on: any_img_selected = True # Tandai bahwa sudah ada yang pilih gambar
            
            req_details.append({"topik": topik, "level": level, "use_image": img_on})

    c1, c2 = st.columns(2)
    if c1.button("🚀 Generate", type="primary"): btn_gen = True
    else: btn_gen = False
    if c2.button("🔄 Reset"):
        st.session_state.hasil_soal = None
        st.session_state.reset_counter += 1
        st.rerun()

# --- 7. MAIN PAGE ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.markdown('<div class="warning-text">⚠️ Batasan: Hanya 1 soal yang bisa menggunakan gambar per sesi agar akurasi tetap terjaga.</div>', unsafe_allow_html=True)
st.write("---")

if btn_gen:
    client = OpenAI(api_key=api_key)
    status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
    
    materi_summary = "\n".join([f"- Soal {i+1}: {r['topik']} ({r['level']})" for i, r in enumerate(req_details)])

    # PERSONA PAKAR & INSTRUKSI DIAGRAM KERAS
    system_prompt = """Anda adalah Pakar Kurikulum Merdeka Kemdikbud RI. 
    ATURAN KETAT MATEMATIKA:
    1. Jika materi adalah 'Diagram Batang' atau 'Diagram Lingkaran', pertanyaan WAJIB tentang 'Membaca Data' dari gambar ilustrasi.
    2. Opsi jawaban HARUS 100% sinkron dengan data yang ada di gambar dan pembahasan.
    3. Pilihan jawaban salah (distraktor) harus logis bagi anak SD.
    4. Seluruh teks wajib Bahasa Indonesia formal. Opsi wajib label A. B. C. D.
    5. 'image_prompt' dlm bahasa Inggris teknis: Deskripsikan grafik batang/lingkaran dengan data spesifik (misal: batang tinggi untuk Apel=10, batang pendek untuk Jeruk=5)."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Kelas: {kelas_sel}, Mapel: {mapel_sel}\n{materi_summary}"}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content).get("soal_list", [])
        
        pb = st.progress(0)
        for i, item in enumerate(data):
            item['materi'], item['level'] = req_details[i]['topik'], req_details[i]['level']
            item['img_url'] = construct_img_url(item['image_prompt']) if req_details[i]['use_image'] else None
            pb.progress(int(((i + 1) / len(data)) * 100))
            
        st.session_state.hasil_soal = data
        status_box.update(label="✅ Selesai!", state="complete", expanded=False)
    except Exception as e: st.error(f"Gagal: {e}")

if st.session_state.hasil_soal:
    st.download_button("📥 Download Word", create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel), f"Soal_{mapel_sel}.docx")
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            st.markdown(f"### Soal {item['no']}\n**{item['soal']}**")
            if item.get('img_url'): st.image(item['img_url'], width=500)
            
            clean_opsi = []
            for i, o in enumerate(item['opsi']):
                lbl = ['A', 'B', 'C', 'D'][i]
                clean_opsi.append(o if o.startswith(lbl) else f"{lbl}. {o}")
            
            pilih = st.radio("Jawaban:", clean_opsi, key=f"ans_{idx}_{suffix}", index=None)
            st.markdown(f"<div class='metadata-text'>Materi: {item['materi']} | Level: {item['level']}</div>", unsafe_allow_html=True)
            
            if pilih:
                if clean_opsi.index(pilih) == item['kunci_index']: st.success("Benar!")
                else: st.error("Salah.")
            with st.expander("Pembahasan"): st.write(item['pembahasan'])

st.markdown("<div style='text-align:center; font-size:12px;'><br><b>Akademi Pelajar © Semua hak cipta dilindungi undang-undang</b></div>", unsafe_allow_html=True)
