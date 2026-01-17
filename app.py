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

# --- 2. STYLE CSS (DIKUNCI TOTAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');

    .header-title { font-family: 'League Spartan', sans-serif; font-size: 32px; font-weight: bold; line-height: 1.2; color: #1E1E1E; }
    .header-sub { font-family: 'Poppins', sans-serif; font-size: 18px; font-weight: bold; font-style: italic; color: #444; margin-bottom: 5px; }
    .warning-text { font-size: 13px; color: #d9534f; font-weight: bold; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #e6f3ff 0%, #ffffff 100%); border-right: 1px solid #d1e3f3; }
    .stRadio [data-testid="stWidgetLabel"] p { font-weight: bold; font-size: 16px; color: #1E1E1E; }
    .metadata-text { font-size: 12px; font-style: italic; color: #555; margin-top: 10px; font-family: 'Poppins', sans-serif; font-weight: bold; }
    div.stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE MATERI ---
DATABASE_MATERI = {
    "1 SD": {
        "Matematika": ["Bilangan sampai 10", "Penjumlahan & Pengurangan", "Bentuk Bangun Datar", "Mengukur Panjang Benda", "Mengenal Waktu"],
        "IPA": ["Anggota Tubuh", "Pancaindra", "Siang dan Malam", "Benda Hidup & Mati"],
        "Bahasa Indonesia": ["Mengenal Huruf", "Suku Kata", "Perkenalan Diri", "Benda di Sekitarku"],
        "Bahasa Inggris": ["Numbers 1-10", "Colors", "My Body", "Greetings"]
    },
    "2 SD": {
        "Matematika": ["Perkalian Dasar", "Pembagian Dasar", "Bangun Datar & Ruang", "Pengukuran Berat (kg, ons)", "Nilai Uang"],
        "IPA": ["Wujud Benda (Padat, Cair, Gas)", "Panas dan Cahaya", "Tempat Hidup Hewan"],
        "Bahasa Indonesia": ["Ungkapan Santun", "Tanda Baca", "Puisi Anak", "Menjaga Kesehatan"],
        "Bahasa Inggris": ["Parts of House", "Daily Activities", "Numbers 11-20", "Animals"]
    },
    "3 SD": {
        "Matematika": ["Pecahan Sederhana", "Simetri & Sudut", "Luas & Keliling Persegi", "Garis Bilangan", "Diagram Gambar"],
        "IPA": ["Ciri-ciri Makhluk Hidup", "Perubahan Wujud Benda", "Cuaca dan Musim", "Energi Alternatif"],
        "Bahasa Indonesia": ["Dongeng Hewan (Fabel)", "Lambang Pramuka", "Denah dan Arah", "Kalimat Saran"],
        "Bahasa Inggris": ["Telling Time", "Days of Week", "Hobby", "Professions"]
    },
    "4 SD": {
        "Matematika": ["Pecahan Senilai", "KPK dan FPB", "Segi Banyak", "Pembulatan Bilangan", "Diagram Batang"],
        "IPA": ["Gaya dan Gerak", "Sumber Energi", "Bunyi dan Pendengaran", "Cahaya", "Pelestarian Alam"],
        "Bahasa Indonesia": ["Gagasan Pokok", "Wawancara", "Puisi", "Teks Non-Fiksi"],
        "Bahasa Inggris": ["My Living Room", "Kitchen Utensils", "Present Continuous", "Transportation"]
    },
    "5 SD": {
        "Matematika": ["Operasi Pecahan", "Kecepatan dan Debit", "Skala dan Denah", "Volume Kubus & Balok", "Jaring-jaring Bangun Ruang"],
        "IPA": ["Organ Pernapasan", "Organ Pencernaan", "Ekosistem", "Panas dan Perpindahannya", "Siklus Air"],
        "Bahasa Indonesia": ["Iklan", "Pantun", "Surat Undangan", "Peristiwa Kebangsaan"],
        "Bahasa Inggris": ["Health Problems", "Ordering Food", "Comparison (Degrees)", "Shape and Size"]
    },
    "6 SD": {
        "Matematika": ["Bilangan Bulat Negatif", "Lingkaran", "Bangun Ruang Campuran", "Modus Median Mean", "Operasi Hitung Campuran"],
        "IPA": ["Perkembangbiakan Makhluk Hidup", "Listrik", "Magnet", "Tata Surya", "Pubertas"],
        "Bahasa Indonesia": ["Teks Laporan", "Pidato", "Formulir", "Teks Eksplanasi"],
        "Bahasa Inggris": ["Simple Past Tense", "Direction", "Government", "Holiday Plan"]
    }
}

# --- 4. FUNGSI LOGIKA GAMBAR ---
def construct_img_url(prompt):
    # Prompt Teknikal: Melarang teks dalam gambar agar tidak ngawur
    full_prompt = f"{prompt}, clear educational illustration, white background, no text inside image, flat vector style"
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
    doc.add_heading('A. SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True
        if item.get('img_url'):
            img_data = safe_download_image(item['img_url'])
            if img_data:
                try: doc.add_picture(img_data, width=Inches(3.0))
                except: pass
        
        labels = ['A', 'B', 'C', 'D']
        for i, op in enumerate(item['opsi']):
            prefix = f"{labels[i]}. "
            text = op if op.startswith(tuple(labels)) else f"{prefix}{op}"
            doc.add_paragraph(text)
        
        meta = doc.add_paragraph(f"Materi: {item['materi']} | Level: {item['level']}")
        meta.italic = True

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN', level=1)
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
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image("logo.png", width=100)
    
    st.markdown("### ⚙️ Konfigurasi")
    if "OPENAI_API_KEY" in st.secrets: api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("OpenAI API Key", type="password", key=f"api_{suffix}")
        if not api_key: st.stop()

    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()), key=f"kelas_{suffix}")
    mapel_sel = st.selectbox("Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()), key=f"mapel_{suffix}")
    jml_soal = st.slider("Jumlah Soal", 1, 5, 2, key=f"jml_{suffix}")

    req_details = []
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=(i==0)):
            topik = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"top_{i}_{suffix}")
            level = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], key=f"lvl_{i}_{suffix}")
            img_on = st.checkbox("Gunakan Gambar", value=(True if i==0 else False), key=f"img_{i}_{suffix}")
            req_details.append({"topik": topik, "level": level, "use_image": img_on})

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1: btn_gen = st.button("🚀 Generate", type="primary")
    with c_btn2:
        if st.button("🔄 Reset"):
            st.session_state.hasil_soal = None
            st.session_state.reset_counter += 1
            st.rerun()

# --- 7. MAIN PAGE ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.markdown('<div class="warning-text">⚠️ Ketentuan: Soal dengan ilustrasi gambar maksimal 1 per sesi agar hasil lebih akurat.</div>', unsafe_allow_html=True)
st.write("---")

if btn_gen:
    client = OpenAI(api_key=api_key)
    status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
    
    materi_summary = ""
    for i, req in enumerate(req_details):
        materi_summary += f"- Soal {i+1}: Materi '{req['topik']}', Level Kesulitan '{req['level']}'\n"

    # PERSONA TAJAM & ATURAN KETAT
    system_prompt = """Anda adalah Pakar Pengembang Kurikulum Merdeka Kemdikbud RI dan Penulis Bank Soal Profesional. 
    Tugas Anda membuat soal pilihan ganda tingkat SD yang berstandar tinggi, relevan, dan edukatif.

    ATURAN KETAT:
    1. BAHASA: Wajib 100% Bahasa Indonesia formal yang sesuai tingkat kognitif anak SD (Fase A/B/C).
    2. FORMAT OPSI: Wajib 4 pilihan diawali label 'A. ', 'B. ', 'C. ', 'D. '.
    3. LOGIKA JAWABAN: Hubungkan data soal dengan opsi secara presisi. Kunci jawaban harus benar sesuai materi.
    4. KUALITAS DISTRAKTOR: Pilihan jawaban salah harus logis dan mengecoh, tidak boleh asal-asalan.
    5. PENDEKATAN HOTS & KONTEKSTUAL: Gunakan narasi kehidupan sehari-hari. Level 'Sulit' wajib menuntut analisis (HOTS).
    6. ATURAN IMAGE PROMPT: 'image_prompt' dlm bahasa Inggris teknis. JANGAN sertakan instruksi teks/tulisan di dalam gambar (No text inside image)."""
    
    user_prompt = f"""
    Mata Pelajaran: {mapel_sel}, Kelas: {kelas_sel}.
    Daftar Materi:
    {materi_summary}
    Berikan output JSON object:
    {{
      "soal_list": [
        {{
          "no": 1,
          "soal": "Pertanyaan Bahasa Indonesia",
          "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
          "kunci_index": 0,
          "pembahasan": "Penjelasan dlm Bahasa Indonesia",
          "image_prompt": "Specific visual details for diagram generation"
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)["soal_list"]
        pb = st.progress(0)
        
        for i, item in enumerate(data):
            item['materi'] = req_details[i]['topik']
            item['level'] = req_details[i]['level']
            item['img_url'] = None
            if i < len(req_details) and req_details[i]['use_image']:
                status_box.write(f"🖼️ Menyusun ilustrasi spesifik materi: {item['materi']}...")
                item['img_url'] = construct_img_url(item.get('image_prompt', 'educational illustration'))
            
            pb.progress(int(((i + 1) / len(data)) * 100))
            time.sleep(0.5)
            
        st.session_state.hasil_soal = data
        pb.empty()
        status_box.update(label="✅ Selesai! Soal siap ditinjau.", state="complete", expanded=False)
        
    except Exception as e:
        status_box.update(label="❌ Terjadi kesalahan", state="error")
        st.error(f"Gagal: {e}")

if st.session_state.hasil_soal:
    df_word = create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel)
    st.download_button("📥 Download Word (.docx)", data=df_word, file_name=f"Soal_{mapel_sel}.docx")
    st.write("---")
    
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            st.markdown(f"### Soal Nomor {item['no']}")
            st.markdown(f"**{item['soal']}**")
            
            if item.get('img_url'):
                st.image(item['img_url'], width=450)
            
            labels = ['A', 'B', 'C', 'D']
            clean_opsi = []
            for i, o in enumerate(item['opsi']):
                prefix = f"{labels[i]}. "
                clean_opsi.append(o if o.startswith(tuple(labels)) else f"{prefix}{o}")

            pilihan = st.radio("Pilih jawaban:", clean_opsi, key=f"ans_{idx}_{st.session_state.reset_counter}", index=None)
            
            # Metadata Note (Bold & Italic)
            st.markdown(f"<div class='metadata-text'>Materi : {item['materi']} | Level : {item['level']}</div>", unsafe_allow_html=True)
            
            if pilihan:
                if clean_opsi.index(pilihan) == item['kunci_index']: st.success("✅ Jawaban Anda Benar!")
                else: st.error("❌ Jawaban Anda Salah.")
            
            with st.expander("Kunci & Pembahasan"):
                st.info(f"Kunci: {clean_opsi[item['kunci_index']]}")
                st.write(item['pembahasan'])

st.write("---")
st.markdown("""
<div style='text-align: center; font-size: 12px;'>
    <b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p></b>
    <b><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p></b>
    <b><p>Semua hak cipta dilindungi undang-undang</p></b>
</div>
""", unsafe_allow_html=True)
