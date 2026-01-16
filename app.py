import streamlit as st
import json
import requests
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
# Model Teks (Soal)
TEXT_MODEL = "gemini-2.5-flash"

# Model Gambar (Sesuai hasil cek akun Anda)
# Jika masih error, nanti otomatis muncul pesan ramah
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

# --- 3. STYLE CSS (ELEGANT CHIC + FIXED SIDEBAR) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@500;700&family=Poppins:wght@400;600;700&display=swap');
    
    /* Sidebar: Biru Sangat Tipis & Lebar Terkunci */
    [data-testid="stSidebar"] {
        background-color: #e6f3ff; 
        border-right: 1px solid #d1e5f0;
        min-width: 320px !important; 
        max-width: 320px !important; 
    }
    
    /* Padding Konten Utama */
    .block-container {
        padding: 20px !important;
    }

    /* Judul Utama: League Spartan 30px */
    h1 { 
        font-family: 'League Spartan', sans-serif !important; 
        font-weight: 700; 
        color: #1a1a1a; 
        font-size: 30px !important; 
        margin-bottom: 5px !important;
    }
    
    /* Subtitle: Poppins 18px */
    .subtitle { 
        font-family: 'Poppins', sans-serif !important; 
        font-size: 18px; 
        color: #666666; 
        margin-top: 0px; 
        margin-bottom: 25px; 
    }
    
    /* Label Input: Bold, Hitam, Uppercase */
    .stSelectbox label, .stTextInput label, .stNumberInput label {
        font-family: 'Poppins', sans-serif !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        color: #000000 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Opsi Jawaban Radio: Normal (Tidak Kapital Semua) */
    .stRadio label {
        font-family: 'Poppins', sans-serif !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        color: #333333 !important;
        text-transform: none !important;
    }
    
    /* Checkbox Label */
    .stCheckbox label {
        font-family: 'Poppins', sans-serif !important;
        color: #000000 !important;
    }
    
    /* Tombol Utama */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3em; 
        font-family: 'Poppins', sans-serif; 
        font-weight: 600; 
        background-color: #2196F3; 
        color: white;
    }
    
    /* Hapus gap di sidebar */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    
    /* Footer Info Kecil di Kartu Soal */
    .footer-info {
        font-family: 'Poppins', sans-serif;
        font-size: 12px;
        color: #888;
        border-top: 1px dashed #ccc;
        padding-top: 5px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI GENERATE GAMBAR (VIA POLLINATIONS.AI - GRATIS & STABIL) ---
def generate_image_google(api_key, image_prompt):
    # Kita beralih ke Pollinations.ai karena Google Imagen sering memblokir akses API Key gratis
    # Layanan ini Gratis, Cepat, dan Aman untuk ilustrasi standar
    
    # 1. Bersihkan prompt agar URL friendly
    clean_prompt = image_prompt.replace(" ", "%20")
    
    # 2. Tambahkan style agar konsisten (Kartun, Vector, Putih)
    style_suffix = "cartoon%20vector%20art%20educational%20illustration%20white%20background"
    
    # 3. Buat URL Request
    # Seed acak agar gambar tidak monoton, tapi kita pakai statis biar stabil
    url = f"https://pollinations.ai/p/{clean_prompt}%20{style_suffix}?width=800&height=800&seed=42&nologo=true"
    
    try:
        # Request Gambar (GET biasa)
        response = requests.get(url, timeout=10) # Timeout 10 detik
        
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            st.warning("⚠️ Gagal mengambil gambar dari server alternatif.")
            return None
            
    except Exception as e:
        st.warning(f"⚠️ Koneksi gambar timeout/error: {str(e)}")
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
        
        # Masukkan Gambar jika ada
        if item.get('image_data'):
            try:
                doc.add_picture(item['image_data'], width=Inches(2.0))
                item['image_data'].seek(0)
            except: pass
        
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

# --- 6. LOGIKA AI ---
def generate_soal_multi_granular(api_key, tipe_soal, kelas, mapel, list_request):
    url_text = f"https://generativelanguage.googleapis.com/v1beta/models/{TEXT_MODEL}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    req_str = ""
    for i, req in enumerate(list_request):
        # Logika Prompt Gambar
        pakai_gambar = "YA (Wajib deskripsi visual)" if req['use_image'] else "TIDAK (Hanya teks)"
        req_str += f"- Soal No {i+1}: Topik '{req['topik']}', Level '{req['level']}', Butuh Gambar? {pakai_gambar}\n"

    if tipe_soal == "Pilihan Ganda":
        json_structure = """[{"no":1,"soal":"...","opsi":["A. Teks...","B. Teks...","C. Teks...","D. Teks..."],"kunci_index":0,"pembahasan":"...","image_prompt": "..."}]"""
    else:
        json_structure = """[{"no":1,"soal":"...","poin_kunci":["..."],"pembahasan":"...","image_prompt": "..."}]"""

    prompt = f"""
    Bertindaklah sebagai Guru SD profesional. Buatkan {len(list_request)} soal {tipe_soal} untuk siswa {kelas} SD Kurikulum Merdeka.
    Mata Pelajaran: {mapel}
    
    Instruksi Per Soal:
    {req_str}
    
    ATURAN SANGAT PENTING:
    1. Jika 'Butuh Gambar: YA', isi field 'image_prompt' dengan deskripsi visual (Inggris). Soal harus merujuk ke gambar.
    2. Jika 'Butuh Gambar: TIDAK', isi 'image_prompt' dengan null.
    3. Opsi Jawaban PG gunakan Sentence case (Huruf besar di awal saja). JANGAN ALL CAPS.
    4. Hindari format LaTeX ($). Gunakan simbol biasa (+, -, x, :).
    
    Output WAJIB JSON Array Murni:
    {json_structure}
    """
    
    try:
        response = requests.post(url_text, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        if response.status_code != 200: return None, f"Error Text API: {response.text}"
        
        teks = response.json()['candidates'][0]['content']['parts'][0]['text']
        clean_json = teks.replace("```json", "").replace("```", "").strip()
        data_soal = json.loads(clean_json)
        
        # --- GENERATE GAMBAR (JIKA ADA PERMINTAAN) ---
        for item in data_soal:
            item['image_data'] = None
            if item.get('image_prompt'):
                # Panggil fungsi gambar yang sudah di-update dengan pesan ramah
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
    # Logo Center
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2: st.image("logo.png", width=100)
    else:
        st.caption("Admin: Upload logo.png")
    
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
    
    # JUMLAH SOAL 1-5
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
        
        # Checkbox Gambar
        use_image = st.checkbox(f"Pakai Gambar?", key=f"img_{i}")
        
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
            with st.spinner("Sedang meracik soal & gambar..."):
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
                
                # Radio Button tanpa pilihan default
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
                if item.get('image_data'):
                    st.image(item['image_data'], caption="Ilustrasi Soal", width=300)

                st.write(f"**Soal {idx+1}:** {item['soal']}")
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                st.text_area("Jawab:", height=80, key=f"essay_{idx}")
                with st.expander("Lihat Kunci Guru"):
                    st.write(item['pembahasan'])

# --- 10. FOOTER COPYRIGHT (FIXED 12PX BOLD CENTER - DEKAT KONTEN) ---
st.markdown("""
<div style='text-align: center; font-size: 12px; font-weight: bold; margin-top: 30px; padding-top: 15px; border-top: 1px solid #e0e0e0; color: #555; font-family: Poppins;'>
    <p style='margin: 3px 0;'>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p>
    <p style='margin: 3px 0;'>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p>
    <p style='margin: 3px 0;'>Semua hak cipta dilindungi undang-undang</p>
</div>
""", unsafe_allow_html=True)

