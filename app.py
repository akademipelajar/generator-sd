import streamlit as st
import json
import requests
import os
from io import BytesIO
from urllib.parse import quote
from docx import Document
from docx.shared import Inches
from openai import OpenAI

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD - Akademi Pelajar",
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
.stButton>button { width: 100%; }
</style>""", unsafe_allow_html=True)

# --- 4. FUNGSI GENERATE GAMBAR (DENGAN VALIDASI) ---
def generate_image_pollinations(image_prompt):
    # Membersihkan prompt agar URL tidak rusak
    clean_prompt = quote(image_prompt + " cartoon vector style, simple education, white background")
    url = f"https://pollinations.ai/p/{clean_prompt}?width=512&height=512&seed=42&nologo=true"
    
    try:
        response = requests.get(url, timeout=20)
        # Validasi: Apakah response benar-benar gambar?
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            return BytesIO(response.content)
        return None
    except:
        return None

# --- 5. FUNGSI GENERATE WORD (FIX UNRECOGNIZED IMAGE ERROR) ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')

    doc.add_heading('A. SOAL PILIHAN GANDA', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = False
        
        # PENANGANAN GAMBAR UNTUK WORD
        if item.get('image_data'):
            try:
                # PENTING: Kembalikan pointer ke awal sebelum dibaca python-docx
                item['image_data'].seek(0) 
                doc.add_picture(item['image_data'], width=Inches(2.5))
            except Exception as e:
                # Jika gambar korup, beri catatan di Word alih-alih crash
                doc.add_paragraph(f"[Gambar tidak dapat dimuat: {item.get('image_prompt', 'Error')}]")
        
        for op in item['opsi']:
            doc.add_paragraph(op, style='List Bullet')

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN & PEMBAHASAN', level=1)
    
    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"Nomor {idx+1}:")
        doc.add_paragraph(f"Kunci: {item['opsi'][item['kunci_index']]}")
        doc.add_paragraph(f"Pembahasan: {item['pembahasan']}")
        doc.add_paragraph("-" * 20)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 6. LOGIKA AI OPENAI ---
def generate_soal_multi_granular(api_key, kelas, mapel, list_request):
    client = OpenAI(api_key=api_key)

    req_str = ""
    for i, req in enumerate(list_request):
        pakai_gambar = "YA" if req['use_image'] else "TIDAK"
        req_str += f"- Soal No {i+1}: Materi '{req['topik']}', Level '{req['level']}', Butuh Gambar? {pakai_gambar}\n"

    prompt = f"""
    Buatkan {len(list_request)} soal pilihan ganda untuk siswa {kelas} SD dalam bahasa Indonesia.
    Mata Pelajaran: {mapel}
    
    Detail per nomor:
    {req_str}

    WAJIB memberikan output JSON murni (tanpa penjelasan tambahan):
    [
      {{
        "no": 1,
        "soal": "...",
        "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "kunci_index": 0,
        "pembahasan": "...",
        "image_prompt": "simple english description of the object/scene for image generation"
      }}
    ]
    """

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        teks = response.choices[0].message.content
        clean = teks.replace("```json", "").replace("```", "").strip()
        data_soal = json.loads(clean)

        # Proses download gambar satu per satu
        for i, item in enumerate(data_soal):
            item['image_data'] = None
            # Hanya download jika user mencentang 'use_image' untuk nomor tersebut
            if i < len(list_request) and list_request[i]['use_image']:
                prompt_gambar = item.get('image_prompt', 'school object')
                img_stream = generate_image_pollinations(prompt_gambar)
                if img_stream:
                    item['image_data'] = img_stream

        return data_soal, None
    except Exception as e:
        return None, str(e)

# --- 7. SESSION STATE ---
if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None

# --- 8. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ KONFIGURASI")
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
        if not api_key: st.stop()

    kelas_sel = st.selectbox("KELAS", list(DATABASE_MATERI.keys()))
    mapel_sel = st.selectbox("MAPEL", list(DATABASE_MATERI[kelas_sel].keys()))
    jml_soal = st.slider("JUMLAH", 1, 5, 2)

    st.divider()
    list_req = []
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}"):
            topik = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t_{i}")
            lvl = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], index=1, key=f"l_{i}")
            img = st.checkbox("Pakai Gambar", key=f"i_{i}")
            list_req.append({"topik": topik, "level": lvl, "use_image": img})

    btn = st.button("🚀 GENERATE", type="primary")

# --- 9. UI UTAMA ---
st.title("Generator Soal SD")

if btn:
    with st.spinner("Sedang meramu soal..."):
        res, err = generate_soal_multi_granular(api_key, kelas_sel, mapel_sel, list_req)
        if res:
            st.session_state.hasil_soal = res
        else:
            st.error(f"Error: {err}")

if st.session_state.hasil_soal:
    # Siapkan Download Button di Atas
    docx_file = create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel)
    st.download_button(
        label="📥 Download Soal (Word)",
        data=docx_file,
        file_name=f"Soal_{mapel_sel}_{kelas_sel}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    st.divider()
    
    # Pratinjau Soal di Layar
    for item in st.session_state.hasil_soal:
        with st.container(border=True):
            st.markdown(f"**Soal No {item['no']}**")
            st.write(item['soal'])
            
            if item.get('image_data'):
                try:
                    # Reset pointer sebelum ditampilkan di Streamlit
                    item['image_data'].seek(0)
                    st.image(item['image_data'], width=300)
                except:
                    st.warning("Gambar gagal ditampilkan di pratinjau.")
            
            for op in item['opsi']:
                st.write(op)
            
            with st.expander("Kunci & Pembahasan"):
                st.info(f"Kunci: {item['opsi'][item['kunci_index']]}")
                st.write(item['pembahasan'])

# FOOTER
st.markdown("<br><hr><center><small>Akademi Pelajar © 2024</small></center>", unsafe_allow_html=True)
