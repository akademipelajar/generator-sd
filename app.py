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

# --- 2. STYLE CSS (Font Custom & UI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');

    .header-title {
        font-family: 'League Spartan', sans-serif;
        font-size: 32px;
        font-weight: bold;
        line-height: 1.2;
    }
    .header-sub {
        font-family: 'Poppins', sans-serif;
        font-size: 18px;
        font-weight: bold;
        font-style: italic;
        color: #333;
        margin-bottom: 20px;
    }
    [data-testid="stSidebar"] { background-color: #f0f7ff; }
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

# --- 4. FUNGSI GAMBAR ---
def construct_img_url(prompt):
    """Membuat URL gambar Pollinations yang valid"""
    # Tambahkan style agar konsisten & edukatif
    full_prompt = f"{prompt}, simple cartoon vector, educational illustration, white background"
    return f"https://image.pollinations.ai/prompt/{quote(full_prompt)}?width=512&height=512&nologo=true&seed=42"

def safe_download_image(url):
    """Mendownload gambar untuk Word dengan validasi format"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
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
        
        # Masukkan Gambar ke Word jika ada
        if item.get('img_url'):
            img_data = safe_download_image(item['img_url'])
            if img_data:
                try:
                    doc.add_picture(img_data, width=Inches(2.5))
                except:
                    pass # Lewati jika format tetap tidak dikenal oleh docx
        
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

# --- 6. SIDEBAR (LOGO DIKUNCI) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image("logo.png", width=100)
    
    st.markdown("### ⚙️ Konfigurasi")
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("Masukkan OpenAI API Key", type="password")
        if not api_key: st.stop()

    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()))
    mapel_sel = st.selectbox("Pilih Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()))
    jml_soal = st.slider("Jumlah Soal", 1, 5, 1)

    req_details = []
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=True):
            topik = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"top_{i}")
            level = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], key=f"lvl_{i}")
            img_on = st.checkbox("Gunakan Gambar", value=True, key=f"img_{i}")
            req_details.append({"topik": topik, "level": level, "use_image": img_on})

    btn_gen = st.button("🚀 Generate Soal", type="primary")

# --- 7. MAIN PAGE ---
# --- HEADER DIKUNCI ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.write("---")

if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None

if btn_gen:
    client = OpenAI(api_key=api_key)
    with st.spinner("Sedang meramu soal..."):
        prompt = f"""Buatkan {jml_soal} soal pilihan ganda SD {kelas_sel} Mapel {mapel_sel}. 
        Output WAJIB JSON murni (list of objects) dengan field: 
        'no', 'soal', 'opsi' (isi 4 string), 'kunci_index', 'pembahasan', 'image_prompt' (deskripsi dlm bhs inggris)."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.replace("```json","").replace("```","").strip()
            data = json.loads(raw)
            
            # Pasangkan URL gambar
            for i, item in enumerate(data):
                item['img_url'] = None
                if req_details[i]['use_image']:
                    item['img_url'] = construct_img_url(item.get('image_prompt', 'simple educational object'))
            
            st.session_state.hasil_soal = data
        except Exception as e:
            st.error(f"Gagal memproses AI: {e}")

if st.session_state.hasil_soal:
    # Tombol Download Word
    docx_file = create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel)
    st.download_button("📥 Download Word (.docx)", data=docx_file, file_name=f"Soal_{mapel_sel}.docx")
    
    st.write("---")
    
    # Menampilkan Soal ke Layar
    for item in st.session_state.hasil_soal:
        with st.container(border=True):
            st.markdown(f"### Soal Nomor {item['no']}")
            st.write(item['soal'])
            
            # Tampilkan Gambar (Langsung via URL agar stabil di Web)
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
