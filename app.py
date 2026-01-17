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
    page_title="Generator Soal SD",
    page_icon="📚",
    layout="wide"
)

# --- 2. STYLE CSS (Font & Footer) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');

    .main-title {
        font-family: 'League Spartan', sans-serif;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: -10px;
    }
    .sub-title {
        font-family: 'Poppins', sans-serif;
        font-size: 18px;
        font-weight: bold;
        font-style: italic;
        color: #555;
    }
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE MATERI ---
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
def get_image_url(prompt):
    """Membuat URL gambar yang valid"""
    base_url = "https://image.pollinations.ai/prompt/"
    style = "cartoon vector simple educational illustration white background"
    clean_prompt = quote(f"{prompt} {style}")
    return f"{base_url}{clean_prompt}?width=512&height=512&nologo=true&seed=123"

def download_image_for_word(url):
    """Khusus untuk mendownload gambar agar bisa masuk ke file Word"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return BytesIO(resp.content)
    except:
        return None
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
        
        # Masukkan gambar jika ada URL-nya
        if item.get('img_url'):
            img_data = download_image_for_word(item['img_url'])
            if img_data:
                try:
                    doc.add_picture(img_data, width=Inches(2.5))
                except:
                    pass
        
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

# --- 6. SIDEBAR ---
with st.sidebar:
    # --- LOGO DIKUNCI ---
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image("logo.png", width=100)
    
    st.markdown("### ⚙️ Konfigurasi")
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("API Key", type="password")
        if not api_key: st.stop()

    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()))
    mapel_sel = st.selectbox("Pilih Mapel", list(DATABASE_MATERI[kelas_sel].keys()))
    jml_soal = st.slider("Jumlah Soal", 1, 5, 1)

    req_list = []
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=True):
            t = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t{i}")
            l = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], key=f"l{i}")
            img = st.checkbox("Gunakan Gambar", value=True, key=f"i{i}")
            req_list.append({"topik": t, "level": l, "use_image": img})

    btn_generate = st.button("🚀 Generate Soal", type="primary")

# --- 7. MAIN UI ---
# --- HEADER DIKUNCI ---
st.markdown('<div class="main-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.write("---")

if 'hasil' not in st.session_state:
    st.session_state.hasil = None

if btn_generate:
    client = OpenAI(api_key=api_key)
    with st.spinner("Sedang meracik soal..."):
        prompt = f"Buatkan {jml_soal} soal pilihan ganda SD {kelas_sel} Mapel {mapel_sel}. Format JSON list [{{'no':1,'soal':'','opsi':['A.','B.'],'kunci':0,'pembahasan':'','image_prompt':'deskripsi gambar dlm bahasa inggris'}}] "
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.replace("```json","").replace("```","").strip()
            data = json.loads(raw)
            
            # Tambahkan URL Gambar
            for i, item in enumerate(data):
                item['img_url'] = None
                if req_list[i]['use_image']:
                    item['img_url'] = get_image_url(item.get('image_prompt', 'educational illustration'))
            
            st.session_state.hasil = data
        except Exception as e:
            st.error(f"Gagal: {e}")

if st.session_state.hasil:
    # Tombol Download
    file_word = create_docx(st.session_state.hasil, mapel_sel, kelas_sel)
    st.download_button("📥 Download Word (.docx)", data=file_word, file_name=f"Soal_{mapel_sel}.docx")
    
    # Menampilkan Soal
    for item in st.session_state.hasil:
        with st.container(border=True):
            st.subheader(f"Soal Nomor {item['no']}")
            st.write(item['soal'])
            
            # Menampilkan Gambar (Langsung via URL agar browser yang memuat)
            if item.get('img_url'):
                st.image(item['img_url'], width=350, caption="Ilustrasi Soal")
            
            for op in item['opsi']:
                st.write(op)
            
            with st.expander("Kunci & Pembahasan"):
                st.success(item['pembahasan'])

# --- 8. FOOTER DIKUNCI ---
st.write("---")
st.markdown("""
<div style='text-align: center; font-size: 12px; font-weight: bold;'>
    <p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p>
    <p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p>
    <p>Semua hak cipta dilindungi undang-undang</p>
</div>
""", unsafe_allow_html=True)
