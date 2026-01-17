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

# --- 2. STYLE CSS (DIKUNCI: Header, Sidebar Gradient, Font) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');

    /* Header Styling */
    .header-title {
        font-family: 'League Spartan', sans-serif;
        font-size: 32px;
        font-weight: bold;
        line-height: 1.2;
        color: #1E1E1E;
    }
    .header-sub {
        font-family: 'Poppins', sans-serif;
        font-size: 18px;
        font-weight: bold;
        font-style: italic;
        color: #444;
        margin-bottom: 20px;
    }

    /* Sidebar Gradient Background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e6f3ff 0%, #ffffff 100%);
        border-right: 1px solid #d1e3f3;
    }

    /* Radio Button Label Styling */
    .stRadio [data-testid="stWidgetLabel"] p {
        font-weight: bold;
        font-size: 16px;
    }
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
    full_prompt = f"{prompt}, simple cartoon vector, educational illustration, white background"
    return f"https://image.pollinations.ai/prompt/{quote(full_prompt)}?width=512&height=512&nologo=true&seed=42"

def safe_download_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
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
        
        if item.get('img_url'):
            img_data = safe_download_image(item['img_url'])
            if img_data:
                try: doc.add_picture(img_data, width=Inches(2.5))
                except: pass
        
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

# --- 6. SIDEBAR (LOGO & CSS DIKUNCI) ---
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
    jml_soal = st.slider("Jumlah Soal", 1, 5, 2)

    req_details = []
    for i in range(jml_soal):
        with st.expander(f"Pengaturan Soal {i+1}", expanded=True):
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
    with st.spinner("Sedang meracik soal pilihan ganda..."):
        # PROMPT DIPERKUAT UNTUK JSON MODE
        prompt = f"""
        Buatkan {jml_soal} soal pilihan ganda untuk SD Kelas {kelas_sel} Mata Pelajaran {mapel_sel}.
        Setiap soal harus memiliki tingkat kesulitan yang berbeda sesuai permintaan.
        
        Berikan output dalam format JSON yang valid:
        {{
          "soal_list": [
            {{
              "no": 1,
              "soal": "isi pertanyaan",
              "opsi": ["A. pilihan", "B. pilihan", "C. pilihan", "D. pilihan"],
              "kunci_index": 0,
              "pembahasan": "isi pembahasan",
              "image_prompt": "simple english description for the picture"
            }}
          ]
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Anda adalah asisten pembuat soal ujian yang hanya menjawab dengan format JSON murni."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} # PAKSA JSON MODE
            )
            
            res_json = json.loads(response.choices[0].message.content)
            data = res_json["soal_list"]
            
            for i, item in enumerate(data):
                item['img_url'] = None
                # Sinkronkan dengan checkbox di sidebar
                if i < len(req_details) and req_details[i]['use_image']:
                    item['img_url'] = construct_img_url(item.get('image_prompt', 'educational illustration'))
            
            st.session_state.hasil_soal = data
        except Exception as e:
            st.error(f"Gagal memproses AI: {e}")

if st.session_state.hasil_soal:
    docx_file = create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel)
    st.download_button("📥 Download Word (.docx)", data=docx_file, file_name=f"Soal_{mapel_sel}.docx")
    
    st.write("---")
    
    # LOOP UNTUK MENAMPILKAN SETIAP SOAL
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            st.markdown(f"### Soal Nomor {item['no']}")
            st.markdown(f"**{item['soal']}**")
            
            if item.get('img_url'):
                st.image(item['img_url'], width=350, caption="Ilustrasi Soal")
            
            # RADIO BUTTON INTERAKTIF
            pilihan = st.radio(
                "Pilih jawaban yang benar:",
                item['opsi'],
                key=f"ans_{idx}",
                index=None
            )
            
            if pilihan:
                idx_user = item['opsi'].index(pilihan)
                if idx_user == item['kunci_index']:
                    st.success("✅ Jawaban Anda Benar!")
                else:
                    st.error("❌ Jawaban Anda Salah.")
            
            with st.expander("Kunci & Pembahasan"):
                st.info(f"Kunci Jawaban: {item['opsi'][item['kunci_index']]}")
                st.write(item['pembahasan'])

# --- 8. FOOTER DIKUNCI (BOLD) ---
st.write("---")
st.markdown("""
<div style='text-align: center; font-size: 12px;'>
    <b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p></b>
    <b><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p></b>
    <b><p>Semua hak cipta dilindungi undang-undang</p></b>
</div>
""", unsafe_allow_html=True)
