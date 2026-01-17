import streamlit as st
import json
import requests
import base64
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os 

from openai import OpenAI


# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- KONFIGURASI MODEL OPENAI ---
TEXT_MODEL = "gpt-4o-mini"


# --- 2. DATABASE MATERI ---
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


# --- 3. STYLE CSS ---
st.markdown("""<style>
[data-testid="stSidebar"] { background-color: #e6f3ff; }
</style>""", unsafe_allow_html=True)


# --- 4. FUNGSI GENERATE GAMBAR ---
def generate_image_google(api_key, image_prompt):
    clean_prompt = image_prompt.replace(" ", "%20")
    style_suffix = "cartoon%20vector%20simple%20educational%20white%20background"
    
    url = f"https://pollinations.ai/p/{clean_prompt}%20{style_suffix}?width=800&height=800&seed=42&nologo=true"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None
    except:
        return None


# --- 5. FUNGSI GENERATE WORD ---
def create_docx(data_soal, tipe, mapel, kelas, list_request):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')

    doc.add_heading('A. SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True 
        
        if item.get('image_data'):
            doc.add_picture(item['image_data'], width=Inches(2.0))
        
        if tipe == "Pilihan Ganda":
            for op in item['opsi']:
                doc.add_paragraph(op)

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN', level=1)
    
    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"No {idx+1}: {item['pembahasan']}")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# --- 6. LOGIKA AI OPENAI ---
def generate_soal_multi_granular(api_key, tipe_soal, kelas, mapel, list_request):

    client = OpenAI(api_key=api_key)

    req_str = ""
    for i, req in enumerate(list_request):
        pakai_gambar = "YA" if req['use_image'] else "TIDAK"
        req_str += f"- Soal No {i+1}: Topik '{req['topik']}', Level '{req['level']}', Butuh Gambar? {pakai_gambar}\n"

    json_structure = """[
      {"no":1,"soal":"...","opsi":["A....","B....","C....","D...."],"kunci_index":0,"pembahasan":"...","image_prompt":"..."}
    ]"""

    prompt = f"""
    Buatkan {len(list_request)} soal {tipe_soal} untuk siswa {kelas}
    Mata Pelajaran: {mapel}

    Detail:
    {req_str}

    Output WAJIB JSON murni:
    {json_structure}
    """

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        teks = response.choices[0].message.content
        clean = teks.replace("```json", "").replace("```", "").strip()

        data_soal = json.loads(clean)

        for item in data_soal:
            item['image_data'] = None
            if item.get('image_prompt'):
                img = generate_image_google(api_key, item['image_prompt'])
                if img:
                    item['image_data'] = img

        return data_soal, None

    except Exception as e:
        return None, str(e)


# --- 7. SESSION STATE ---
if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None
if 'tipe_aktif' not in st.session_state:
    st.session_state.tipe_aktif = None


# --- 8. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image("logo.png", width=100)
    
    st.markdown("<h3 style='text-align: center; font-family: League Spartan; font-size:18px; margin-top:0;'>KONFIGURASI UTAMA<br>PANEL GURU</h3>", unsafe_allow_html=True)

    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        st.error("API KEY belum disetting di Streamlit Secrets")
        st.stop()

    kelas = st.selectbox("KELAS", [f"{i} SD" for i in range(1, 7)])
    mapel = st.selectbox("MATA PELAJARAN", ["Matematika", "IPA", "Bahasa Indonesia", "Bahasa Inggris"])

    jml_soal = st.selectbox("JUMLAH SOAL", [1,2,3,4,5])

    list_request_user = []
    for i in range(jml_soal):
        topik = st.selectbox(f"Materi {i+1}", DATABASE_MATERI[kelas][mapel])
        level = st.selectbox(f"Level {i+1}", ["Mudah","Sedang","Sulit"], key=f"lvl_{i}")
        img = st.checkbox("Pakai Gambar?", key=f"img_{i}")

        list_request_user.append({"topik": topik, "level": level, "use_image": img})


# --- 9. UI UTAMA ---
st.title("Generator Soal SD")

if st.button("Generate Soal"):
    res, err = generate_soal_multi_granular(api_key, "Pilihan Ganda", kelas, mapel, list_request_user)
    if res:
        st.session_state.hasil_soal = res
        st.session_state.tipe_aktif = "PG"
    else:
        st.error(err)

if st.session_state.hasil_soal:
    data = st.session_state.hasil_soal
    docx = create_docx(data, "Pilihan Ganda", mapel, kelas, list_request_user)
    st.download_button("Download Word", docx)


# --- 10. FOOTER COPYRIGHT ---
st.markdown("""
<div style='text-align: center; font-size: 12px; font-weight: bold;'>
    <p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p>
    <p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p>
    <p>Semua hak cipta dilindungi undang-undang</p>
</div>
""", unsafe_allow_html=True)
