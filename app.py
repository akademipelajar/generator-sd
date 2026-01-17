import streamlit as st
import json
import requests
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
OPENAI_MODEL = "gpt-4o-mini"


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
    
    .stSelectbox label, .stTextInput label {
        font-size: 13px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

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


# --- 4. FUNGSI GENERATE GAMBAR (POLLINATIONS - GRATIS) ---
def generate_image(image_prompt):
    try:
        clean_prompt = image_prompt.replace(" ", "%20")
        style_suffix = "cartoon%20vector%20simple%20educational%20white%20background"
        url = f"https://pollinations.ai/p/{clean_prompt}%20{style_suffix}?width=800&height=800&seed=42&nologo=true"

        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None
    except:
        return None


# --- 5. FUNGSI GENERATE WORD (DOCX) ---
def create_docx(data_soal, tipe, mapel, kelas):
    doc = Document()

    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_paragraph('_' * 60)

    doc.add_heading('A. SOAL', level=1)

    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True

        if item.get('image_data'):
            doc.add_picture(item['image_data'], width=Inches(2.0))

        if tipe == "Pilihan Ganda":
            for op in item['opsi']:
                doc.add_paragraph(op)

        doc.add_paragraph()

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN', level=1)

    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"No {idx+1}")
        doc.add_paragraph(item['pembahasan'])
        doc.add_paragraph("-" * 20)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# --- 6. LOGIKA AI OPENAI ---
def generate_soal_openai(api_key, tipe_soal, kelas, mapel, list_request):

    client = OpenAI(api_key=api_key)

    req_str = ""
    for i, req in enumerate(list_request):
        pakai_gambar = "YA" if req['use_image'] else "TIDAK"
        req_str += f"- Soal {i+1}: Topik '{req['topik']}', Level '{req['level']}', Gambar? {pakai_gambar}\n"

    json_structure = """
    [
      {
        "no":1,
        "soal":"...",
        "opsi":["A....","B....","C....","D...."],
        "kunci_index":0,
        "pembahasan":"...",
        "image_prompt":"..."
      }
    ]
    """

    prompt = f"""
    Kamu adalah guru SD profesional.

    Buatkan {len(list_request)} soal {tipe_soal}
    Kelas: {kelas}
    Mata Pelajaran: {mapel}

    Detail:
    {req_str}

    Aturan:
    - Bahasa Indonesia yang mudah dipahami
    - Jika perlu gambar, isi image_prompt dalam Bahasa Inggris sederhana
    - Output wajib JSON murni

    Format:
    {json_structure}
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Kamu pembuat soal SD profesional."},
                {"role": "user", "content": prompt}
            ]
        )

        teks = response.choices[0].message.content
        clean = teks.replace("```json", "").replace("```", "").strip()

        data_soal = json.loads(clean)

        for item in data_soal:
            item["image_data"] = None
            if item.get("image_prompt"):
                img = generate_image(item["image_prompt"])
                if img:
                    item["image_data"] = img

        return data_soal, None

    except Exception as e:
        return None, str(e)


# --- 7. SESSION STATE ---
if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None


# --- 8. SIDEBAR ---
with st.sidebar:

    st.title("KONFIGURASI UTAMA PANEL GURU & MENTOR")

    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("Terhubung ke OpenAI ✔")
    else:
        st.error("OPENAI_API_KEY belum disetting di Streamlit Secrets")
        st.stop()

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
        if not api_key: st.error("Masukkan OpenAI API Key dulu!")
        else:
            with st.spinner("Sedang meracik soal (Powered by OpenAI)..."):
                res, err = generate_soal_openai(api_key, "Pilihan Ganda", kelas, mapel, list_request_user)
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
                if item.get('image_data'):
                    st.image(item['image_data'], caption="Ilustrasi Soal", width=300)
                elif item.get('image_prompt') and info_req['use_image']:
                    st.warning("⚠️ Gagal memuat gambar (Koneksi Pollinations).")
                
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
        if not api_key: st.error("Masukkan OpenAI API Key dulu!")
        else:
            with st.spinner("Sedang membuat soal uraian..."):
                res, err = generate_soal_openai(api_key, "Uraian", kelas, mapel, list_request_user)
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


# --- 10. FOOTER COPYRIGHT ---
st.markdown("""
<div style='text-align: center; font-size: 12px; font-weight: bold; margin-top: 30px; padding-top: 15px; border-top: 1px solid #e0e0e0; color: #555; font-family: Poppins;'>
    <p style='margin: 3px 0;'>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p>
    <p style='margin: 3px 0;'>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p>
    <p style='margin: 3px 0;'>Semua hak cipta dilindungi undang-undang</p>
</div>
""", unsafe_allow_html=True)

