import streamlit as st
import json
import requests
import time
import base64
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- KONFIGURASI MODEL ---
TEXT_MODEL = "gemini-2.5-flash"
# Gunakan model gambar yang muncul di hasil cek Anda kemarin
IMAGE_MODEL = "imagen-3.0-generate-001" 

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
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@500;700&family=Poppins:wght@400;600;700&display=swap');
    
    [data-testid="stSidebar"] {
        background-color: #e6f3ff; 
        border-right: 1px solid #d1e5f0;
        min-width: 320px !important; 
        max-width: 320px !important; 
    }
    
    .block-container { padding: 20px !important; }

    h1 { 
        font-family: 'League Spartan', sans-serif !important; 
        font-weight: 700; color: #1a1a1a; font-size: 30px !important; margin-bottom: 5px !important;
    }
    
    .subtitle { 
        font-family: 'Poppins', sans-serif !important; font-size: 18px; color: #666666; margin-top: 0px; margin-bottom: 25px; 
    }
    
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stRadio label, .stCheckbox label {
        font-family: 'Poppins', sans-serif !important;
        color: #000000 !important;
    }
    
    /* Label Input Sidebar Besar & Bold */
    .stSelectbox label, .stTextInput label {
        font-size: 13px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Opsi Jawaban Normal */
    .stRadio label {
        font-size: 15px !important;
        font-weight: 400 !important;
        text-transform: none !important;
    }
    
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3em; 
        font-family: 'Poppins', sans-serif; font-weight: 600; 
        background-color: #2196F3; color: white;
    }
    
    .footer-info {
        font-family: 'Poppins', sans-serif; font-size: 12px; color: #888;
        border-top: 1px dashed #ccc; padding-top: 5px; margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI GENERATE GAMBAR (IMAGEN) ---
def generate_image_google(api_key, image_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{IMAGE_MODEL}:predict?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Prompt style kartun edukasi agar ramah anak
    full_prompt = f"Educational illustration for elementary school exam, vector art style, white background, clear lines: {image_prompt}"
    
    payload = {
        "instances": [{"prompt": full_prompt}],
        "parameters": {"sampleCount": 1}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None
        
        result = response.json()
        # Ambil data base64
        b64_data = result['predictions'][0]['bytesBase64Encoded']
        # Convert ke BytesIO (agar bisa dibaca Streamlit & Word)
        image_bytes = base64.b64decode(b64_data)
        return BytesIO(image_bytes)
    except:
        return None

# --- 5. FUNGSI GENERATE WORD (DOCX) ---
def create_docx(data_soal, tipe, mapel, kelas, list_request):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    judul = doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    judul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_paragraph('_' * 70)

    doc.add_heading('A. SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        req_data = list_request[idx]
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True 
        
        # --- MASUKKAN GAMBAR KE WORD JIKA ADA ---
        if item.get('image_data'):
            # Resize image agar pas di kertas (misal lebar 2.5 inch)
            doc.add_picture(item['image_data'], width=Inches(2.5))
            # Reset pointer agar gambar bisa dipakai lagi (jika perlu)
            item['image_data'].seek(0)
        
        if tipe == "Pilihan Ganda":
            for op in item['opsi']: doc.add_paragraph(f"    {op}")
        else:
            doc.add_paragraph("\n" * 5) 

        p_footer = doc.add_paragraph(f"Materi: {req_data['topik']} | Level: {req_data['level']}")
        p_footer.italic = True
        p_footer.style.font.size = Pt(9)
        p_footer.style.font.color.rgb = RGBColor(100, 100, 100)
        doc.add_paragraph()

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN', level=1)
    
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

# --- 6. LOGIKA AI UTAMA (TEXT + IMAGE COORDINATOR) ---
def generate_soal_multi_granular(api_key, tipe_soal, kelas, mapel, list_request):
    # 1. TEXT GENERATION
    url_text = f"https://generativelanguage.googleapis.com/v1beta/models/{TEXT_MODEL}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    req_str = ""
    for i, req in enumerate(list_request):
        # Cek apakah user minta gambar untuk nomor ini?
        pakai_gambar = "YA (Buatkan deskripsi visual)" if req['use_image'] else "TIDAK (Hanya teks)"
        req_str += f"- Soal No {i+1}: Topik '{req['topik']}', Level '{req['level']}', Butuh Gambar? {pakai_gambar}\n"

    # Struktur JSON dinamis
    json_fields = '"no":1,"soal":"...","pembahasan":"..."'
    if tipe_soal == "Pilihan Ganda":
        json_fields += ',"opsi":["A. ...","B. ...","C. ...","D. ..."],"kunci_index":0'
    else:
        json_fields += ',"poin_kunci":["..."]'
        
    # Tambahkan field 'image_prompt'
    json_fields += ',"image_prompt": "Deskripsi visual dalam bahasa inggris (jika butuh gambar), atau null (jika tidak)"'

    prompt = f"""
    Bertindaklah sebagai Guru SD profesional. Buatkan {len(list_request)} soal {tipe_soal} untuk siswa {kelas} SD Kurikulum Merdeka.
    Mata Pelajaran: {mapel}
    
    Instruksi Per Soal:
    {req_str}
    
    ATURAN KHUSUS:
    1. Jika diminta 'Butuh Gambar: YA', buatlah soal yang merujuk pada gambar tersebut (contoh: "Perhatikan gambar di bawah..."). 
       Lalu isi field 'image_prompt' dengan deskripsi gambar yang detail dalam Bahasa Inggris untuk generator gambar.
    2. Jika 'Butuh Gambar: TIDAK', buat soal cerita deskriptif biasa. Isi 'image_prompt' dengan null.
    3. Pilihan Ganda (PG) jangan ALL CAPS. Gunakan Sentence case.
    4. Hindari LaTeX ($).
    
    Output JSON Array Murni:
    [ {{ {json_fields} }} ]
    """
    
    try:
        # Step A: Generate Text Soal
        response = requests.post(url_text, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        if response.status_code != 200: return None, f"Error Text API: {response.text}"
        
        text_raw = response.json()['candidates'][0]['content']['parts'][0]['text']
        clean_json = text_raw.replace("```json", "").replace("```", "").strip()
        data_soal = json.loads(clean_json)
        
        # Step B: Generate Image (Jika ada request)
        for item in data_soal:
            item['image_data'] = None # Default kosong
            
            # Cek apakah AI memberikan prompt gambar
            if item.get('image_prompt'):
                # Panggil Fungsi Gambar
                img_bytes = generate_image_google(api_key, item['image_prompt'])
                if img_bytes:
                    item['image_data'] = img_bytes
                
        return data_soal, None

    except Exception as e: return None, str(e)

# --- 7. SESSION STATE ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'tipe_aktif' not in st.session_state: st.session_state.tipe_aktif = None

# --- 8. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image("logo.png", width=100)
    
    st.markdown("<h3 style='text-align: center; font-family: League Spartan; font-size:18px; margin-top:0;'>KONFIGURASI UTAMA<br>PANEL GURU</h3>", unsafe_allow_html=True)
    
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.text_input("🔑 API KEY", type="password")

    with st.expander("🕵️ Cek Fitur"):
        if st.button("Cek Imagen"):
            if not api_key: st.error("No Key")
            else:
                try:
                    res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
                    if res.status_code == 200:
                        found = any('image' in m['name'] for m in res.json().get('models', []))
                        if found: st.success("✅ Imagen Aktif!")
                        else: st.warning("❌ Tidak ada Imagen")
                except: pass

    st.markdown("---") 
    
    kelas = st.selectbox("KELAS", [f"{i} SD" for i in range(1, 7)], index=5)
    mapel = st.selectbox("MATA PELAJARAN", ["Matematika", "IPA", "Bahasa Indonesia", "Bahasa Inggris"])
    
    st.divider()
    
    jml_soal = st.selectbox("JUMLAH SOAL", [1, 2, 3, 4, 5])
    
    list_request_user = [] 
    
    st.markdown("<br><div style='font-weight:bold; font-size:14px; border-bottom:1px solid #ccc; margin-bottom:10px; color:#333;'>KONFIGURASI PER SOAL</div>", unsafe_allow_html=True)
    
    for i in range(jml_soal):
        st.markdown(f"**# Soal {i+1}**")
        
        daftar_materi = DATABASE_MATERI.get(kelas, {}).get(mapel, [])
        if daftar_materi: 
            topik_selected = st.selectbox(f"MATERI SOAL {i+1}", daftar_materi, key=f"topik_{i}")
        else: 
            topik_selected = st.text_input(f"MATERI SOAL {i+1} (Manual)", key=f"topik_{i}")
            
        level_selected = st.selectbox(f"LEVEL SOAL {i+1}", ["Mudah", "Sedang", "Sulit (HOTS)"], key=f"lvl_{i}")
        
        # --- NEW: CHECKBOX GAMBAR ---
        use_image = st.checkbox(f"Pakai Gambar?", key=f"img_{i}", help="Centang jika ingin soal ini memiliki ilustrasi gambar")
        
        list_request_user.append({
            "topik": topik_selected, 
            "level": level_selected,
            "use_image": use_image
        })
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    if st.button("🗑️ Reset"):
        st.session_state.hasil_soal = None
        st.rerun()

# --- 9. UI UTAMA ---
st.markdown("<h1>Generator Soal Sekolah Dasar (SD)</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)

tab_pg, tab_uraian = st.tabs(["📝 Pilihan Ganda", "✍️ Soal Uraian"])

# === TAB PG ===
with tab_pg:
    if st.button("🚀 Generate Soal PG", type="primary"):
        if not api_key: st.error("API Key belum diisi")
        else:
            with st.spinner("Sedang meracik soal & menggambar ilustrasi (mohon tunggu)..."):
                res, err = generate_soal_multi_granular(api_key, "Pilihan Ganda", kelas, mapel, list_request_user)
                if res:
                    st.session_state.hasil_soal = res
                    st.session_state.tipe_aktif = "PG"
                else: st.error(err)

    if st.session_state.hasil_soal and st.session_state.tipe_aktif == "PG":
        data = st.session_state.hasil_soal
        docx = create_docx(data, "Pilihan Ganda", mapel, kelas, list_request_user)
        st.download_button("📥 Download Word (.docx)", docx, file_name=f"Soal_PG_{mapel}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        for idx, item in enumerate(data):
            info_req = list_request_user[idx]
            with st.container(border=True):
                # TAMPILKAN GAMBAR JIKA ADA
                if item.get('image_data'):
                    st.image(item['image_data'], caption="Ilustrasi Soal", width=300)
                
                st.write(f"{idx+1}. {item['soal']}") 
                
                ans = st.radio(
                    f"Label_hidden_{idx}",
                    item['opsi'], 
                    key=f"rad_{idx}", 
                    index=None,
                    label_visibility="collapsed"
                )
                
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                with st.expander("Kunci Jawaban"):
                    if ans is None: st.info("Pilih jawaban dulu.")
                    else:
                        kunci = item['opsi'][item['kunci_index']]
                        if ans == kunci: st.success("Benar!")
                        else: st.error(f"Salah. Kunci: {kunci}")
                        st.write(f"**Pembahasan:** {item['pembahasan']}")

# === TAB URAIAN ===
with tab_uraian:
    if st.button("🚀 Generate Soal Uraian", type="primary"):
        if not api_key: st.error("API Key kosong")
        else:
            with st.spinner("Sedang membuat soal & gambar..."):
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
                # TAMPILKAN GAMBAR JIKA ADA
                if item.get('image_data'):
                    st.image(item['image_data'], caption="Ilustrasi Soal", width=300)

                st.write(f"**Soal {idx+1}:** {item['soal']}")
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                st.text_area("Jawab:", height=80, key=f"essay_{idx}")
                with st.expander("Lihat Kunci Guru"):
                    st.write(item['pembahasan'])

# --- 10. FOOTER COPYRIGHT (UPDATED) ---
st.markdown("""
<div style='text-align: center; font-size: 12px; font-weight: bold; margin-top: 20px; padding-top: 10px; border-top: 1px solid #e0e0e0; color: #555; font-family: Poppins;'>
    <p style='margin: 5px 0;'>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p>
    <p style='margin: 5px 0;'>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p>
    <p style='margin: 5px 0;'>Semua hak cipta dilindungi undang-undang</p>
</div>
""", unsafe_allow_html=True)
