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

# --- 4. FUNGSI GENERATE GAMBAR (POLLINATIONS) ---
def generate_image_google(image_prompt):
    # Menggunakan quote untuk handle spasi dan karakter khusus di URL
    clean_prompt = quote(image_prompt + " cartoon vector simple educational white background")
    url = f"https://pollinations.ai/p/{clean_prompt}?width=600&height=600&seed=42&nologo=true"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None
    except:
        return None

# --- 5. FUNGSI GENERATE WORD ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')

    doc.add_heading('A. SOAL PILIHAN GANDA', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = False
        
        if item.get('image_data'):
            # Insert gambar ke Word
            doc.add_picture(item['image_data'], width=Inches(2.5))
        
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
    Buatkan {len(list_request)} soal pilihan ganda untuk siswa {kelas} SD.
    Mata Pelajaran: {mapel}
    
    Detail per nomor:
    {req_str}

    WAJIB memberikan output dalam format JSON murni dengan struktur seperti ini:
    [
      {{
        "no": 1,
        "soal": "Pertanyaan...",
        "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "kunci_index": 0,
        "pembahasan": "Penjelasan...",
        "image_prompt": "deskripsi gambar singkat dalam bahasa inggris jika butuh gambar, jika tidak kosongkan"
      }}
    ]
    """

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "Anda adalah guru SD ahli pembuat soal evaluasi yang kreatif dan akurat."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" } if "gpt-4" in TEXT_MODEL else None
        )

        teks = response.choices[0].message.content
        # Pembersihan teks jika AI memberikan markdown
        clean = teks.replace("```json", "").replace("```", "").strip()
        
        # Load JSON
        data_soal = json.loads(clean)
        if isinstance(data_soal, dict) and "soal" in data_soal: # Handle jika AI return satu object berisi list
             data_soal = data_soal.get("soal", [data_soal])
        elif isinstance(data_soal, dict):
             # Jika JSON dibungkus key lain
             key = list(data_soal.keys())[0]
             data_soal = data_soal[key]

        # Generate Gambar jika diminta
        for i, item in enumerate(data_soal):
            item['image_data'] = None
            # Cek di list_request apakah nomor ini butuh gambar
            if i < len(list_request) and list_request[i]['use_image']:
                if item.get('image_prompt'):
                    img_bytes = generate_image_google(item['image_prompt'])
                    item['image_data'] = img_bytes

        return data_soal, None

    except Exception as e:
        return None, str(e)

# --- 7. SESSION STATE (PENTING AGAR DATA TIDAK HILANG) ---
if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None
if 'list_req' not in st.session_state:
    st.session_state.list_req = []

# --- 8. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    
    st.markdown("### ⚙️ KONFIGURASI PANEL")

    # Cek API Key
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("Masukkan OpenAI API Key", type="password")
        if not api_key:
            st.warning("Masukkan API Key untuk memulai")
            st.stop()

    kelas_sel = st.selectbox("PILIH KELAS", list(DATABASE_MATERI.keys()))
    mapel_sel = st.selectbox("MATA PELAJARAN", list(DATABASE_MATERI[kelas_sel].keys()))
    jml_soal = st.slider("JUMLAH SOAL", 1, 5, 2)

    st.divider()
    
    list_request_user = []
    for i in range(jml_soal):
        with st.expander(f"Pengaturan Soal {i+1}", expanded=(i==0)):
            topik = st.selectbox(f"Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"topik_{i}")
            level = st.select_slider(f"Kesulitan", ["Mudah", "Sedang", "Sulit"], value="Sedang", key=f"lvl_{i}")
            img = st.checkbox("Gunakan Gambar ilustrasi?", key=f"img_{i}")
            list_request_user.append({"topik": topik, "level": level, "use_image": img})

    btn_generate = st.button("🚀 GENERATE SOAL SEKARANG", type="primary")

# --- 9. UI UTAMA & LOGIKA TAMPILAN ---
st.title("📝 Generator Soal SD Digital")
st.caption(f"Menggunakan Model: {TEXT_MODEL} | Pollinations AI Image")

if btn_generate:
    with st.spinner("Sedang memproses soal dan gambar..."):
        res, err = generate_soal_multi_granular(api_key, kelas_sel, mapel_sel, list_request_user)
        if res:
            st.session_state.hasil_soal = res
            st.session_state.list_req = list_request_user # simpan info tambahan
            st.success("Berhasil membuat soal!")
        else:
            st.error(f"Gagal generate: {err}")

# Tampilkan Hasil jika sudah ada di session state
if st.session_state.hasil_soal:
    st.divider()
    
    # Kolom untuk tombol download di bagian atas pratinjau
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🔍 Pratinjau Soal")
    with col2:
        # Proses file Word
        docx_data = create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel)
        st.download_button(
            label="📥 Download Word (.docx)",
            data=docx_data,
            file_name=f"Soal_{mapel_sel}_{kelas_sel}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            help="Klik untuk mendownload file dalam format Microsoft Word"
        )

    # Loop untuk menampilkan isi soal ke layar
    for item in st.session_state.hasil_soal:
        with st.container(border=True):
            st.markdown(f"#### Soal No {item['no']}")
            st.write(item['soal'])
            
            # Tampilkan gambar jika ada
            if item.get('image_data'):
                # Perlu reset pointer stream jika dibaca berulang kali
                item['image_data'].seek(0)
                st.image(item['image_data'], width=300, caption=f"Ilustrasi Soal {item['no']}")
            
            # Tampilkan Opsi
            cols = st.columns(2)
            for i, opsi in enumerate(item['opsi']):
                cols[i % 2].info(opsi)
            
            with st.expander("Kunci Jawaban & Pembahasan"):
                st.success(f"**Kunci:** {item['opsi'][item['kunci_index']]}")
                st.write(f"**Pembahasan:** {item['pembahasan']}")

else:
    # Tampilan awal jika belum generate
    st.info("Silakan atur konfigurasi di sidebar kiri dan klik tombol 'Generate Soal'.")

# --- 10. FOOTER ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 11px;'>
    <p>© 2026 Akademi Pelajar - Sistem Generator Soal Otomatis</p>
    <p>Dilarang menyebarluaskan tanpa izin tertulis.</p>
</div>
""", unsafe_allow_html=True)
