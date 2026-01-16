import streamlit as st
import json
import requests
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator Soal SD Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL_NAME = "gemini-2.5-flash"

# --- 2. DATABASE MATERI LENGKAP (KURIKULUM MERDEKA FASE A, B, C) ---
DATABASE_MATERI = {
    "1 SD": {
        "Matematika": [
            "Bilangan sampai 10 (Menghitung & Menulis)",
            "Menguraikan dan Menyusun Bilangan",
            "Penjumlahan (Bilangan sampai 10)",
            "Pengurangan (Bilangan sampai 10)",
            "Bentuk Bangun Datar (Segitiga, Segiempat, Lingkaran)",
            "Bilangan sampai 20",
            "Jam dan Waktu (Membaca Jam Sederhana)",
            "Membandingkan Ukuran (Panjang/Pendek, Berat/Ringan)",
            "Penjumlahan dan Pengurangan (Bilangan sampai 20)"
        ],
        "IPA": [
            "Anggota Tubuh dan Pancaindra",
            "Merawat Tubuh Kita",
            "Siang dan Malam",
            "Benda Langit (Matahari, Bulan, Bintang)",
            "Hewan dan Tumbuhan di Sekitar Rumah",
            "Benda Hidup dan Benda Mati"
        ],
        "Bahasa Indonesia": [
            "Bunyi Apa? (Mengenal Huruf & Suku Kata)",
            "Ayo Bermain (Tempat dan Aturan Bermain)",
            "Awas Kuman (Kebersihan Diri)",
            "Aku Bisa (Gerakan dan Kegiatan)",
            "Teman Baru (Perkenalan Diri)",
            "Benda di Sekitarku (Deskripsi Benda)"
        ],
        "Bahasa Inggris": [
            "Greetings and Introductions",
            "Numbers 1-10",
            "Colors",
            "My Body",
            "My Family",
            "Animals around us",
            "Fruits and Vegetables"
        ]
    },
    "2 SD": {
        "Matematika": [
            "Bilangan sampai 50",
            "Penjumlahan dan Pengurangan Bersusun",
            "Bentuk Bangun Datar dan Bangun Ruang Sederhana",
            "Posisi Benda dan Pola Gambar",
            "Perkalian Dasar (Konsep Penjumlahan Berulang)",
            "Pembagian Dasar (Pengurangan Berulang)",
            "Waktu dan Durasi (Jam, Menit, Hari)",
            "Bilangan sampai 1.000",
            "Pengukuran Panjang (cm, m) dan Berat (kg, ons)"
        ],
        "IPA": [
            "Wujud Benda (Padat, Cair, Gas)",
            "Perubahan Wujud Benda",
            "Sumber Energi (Panas dan Cahaya)",
            "Matahari dan Bayangan",
            "Bagian Tubuh Hewan dan Tumbuhan",
            "Lingkungan Sehat dan Tidak Sehat"
        ],
        "Bahasa Indonesia": [
            "Mengenal Perasaan (Senang, Sedih, Takut)",
            "Menjaga Kesehatan (Makan Sehat, Olahraga)",
            "Berhati-hati di Mana Saja (Rambu Lalu Lintas)",
            "Keluargaku Unik (Profesi dan Kebiasaan)",
            "Berteman dalam Keragaman",
            "Bijak Memakai Uang"
        ],
        "Bahasa Inggris": [
            "Do you like apple? (Likes & Dislikes)",
            "My Father likes Watermelon (Family's Hobbies)",
            "Where is my pen? (Prepositions: in, on, under)",
            "Numbers 11-20",
            "My School Activities",
            "Parts of the House"
        ]
    },
    "3 SD": {
        "Matematika": [
            "Bilangan Cacah sampai 1.000 (Nilai Tempat)",
            "Operasi Penjumlahan & Pengurangan (Simpan/Pinjam)",
            "Perkalian dan Pembagian Bilangan Cacah",
            "Kalimat Matematika (Masalah Sehari-hari)",
            "Pengukuran Panjang dan Berat (Satuan Baku)",
            "Pecahan Sederhana (1/2, 1/3, 1/4)",
            "Simetri Lipat dan Simetri Putar",
            "Luas dan Keliling (Persegi & Persegi Panjang)",
            "Data dan Diagram Gambar"
        ],
        "IPA": [
            "Mari Kenali Hewan (Karnivora, Herbivora, Omnivora)",
            "Siklus Hidup Makhluk Hidup",
            "Sifat Benda dan Perubahannya",
            "Energi dan Perubahannya",
            "Gaya dan Gerak",
            "Kenampakan Permukaan Bumi"
        ],
        "Bahasa Indonesia": [
            "Bermain di Lingkunganku",
            "Menyayangi Tumbuhan dan Hewan",
            "Benda di Sekitarku (Bahan Pembuat Benda)",
            "Kewajiban dan Hakku",
            "Cuaca dan Perubahan Cuaca",
            "Energi dan Perubahannya",
            "Perkembangan Teknologi"
        ],
        "Bahasa Inggris": [
            "My Name is Made (Introductions & Hobbies)",
            "I Love Reading (Days of the Week)",
            "It is 9 O'clock (Telling Time)",
            "I have breakfast (Daily Routines)",
            "She is a Doctor (Professions)",
            "Weather (Hot, Cold, Rainy)"
        ]
    },
    "4 SD": {
        "Matematika": [
            "Bilangan Cacah Besar (sampai 10.000)",
            "Pembagian dengan Bilangan Satu Angka",
            "Sudut (Pengukuran dan Jenis Sudut)",
            "Pembagian dengan Bilangan Dua Angka",
            "Diagram Garis dan Batang",
            "Faktor dan Kelipatan (FPB & KPK Sederhana)",
            "Pecahan (Senilai, Desimal, Persen)",
            "Luas dan Keliling Bangun Datar Gabungan"
        ],
        "IPA": [
            "Tumbuhan Sumber Kehidupan (Fotosintesis)",
            "Wujud Zat dan Perubahannya",
            "Gaya di Sekitar Kita (Magnet, Gravitasi, Gesek)",
            "Mengubah Bentuk Energi",
            "Cerita Tentang Daerahku (Kearifan Lokal)",
            "Indonesiaku Kaya Budaya"
        ],
        "Bahasa Indonesia": [
            "Sudah Besar (Kata Kerja Transitif/Intransitif)",
            "Di Bawah Atap (Kata Penghubung)",
            "Lihat Sekitar (Rute dan Denah)",
            "Meliuk dan Menerjang (Wawancara)",
            "Bertukar atau Membayar (Literasi Keuangan)",
            "Satu Titik (Kalimat Efektif)"
        ],
        "Bahasa Inggris": [
            "What are you doing? (Present Continuous)",
            "There are some flowers (Quantifiers)",
            "My Living Room (Things in the house)",
            "Cici Cooks in the Kitchen",
            "I Can Ride a Bike (Ability)",
            "Does he study? (Simple Present Tense)"
        ]
    },
    "5 SD": {
        "Matematika": [
            "Bilangan Cacah sampai 1.000.000",
            "KPK dan FPB (Penyelesaian Masalah)",
            "Operasi Hitung Pecahan (Penjumlahan & Pengurangan)",
            "Perkalian dan Pembagian Pecahan",
            "Keliling dan Luas Bangun Datar",
            "Sudut dan Jenis Segitiga",
            "Perbandingan dan Skala",
            "Bangun Ruang (Kubus dan Balok)",
            "Pengumpulan dan Penyajian Data"
        ],
        "IPA": [
            "Cahaya dan Sifatnya",
            "Bunyi dan Pendengaran",
            "Harmoni Ekosistem (Rantai Makanan)",
            "Magnet dan Listrik Sederhana",
            "Pernapasan Manusia dan Hewan",
            "Pencernaan Manusia dan Kesehatan"
        ],
        "Bahasa Indonesia": [
            "Aku yang Unik (Kata Sifat, Sinonim/Antonim)",
            "Buku Jendela Dunia (Teks Fiksi/Non-fiksi)",
            "Ekspresi Diri Melalui Hobi (Imbuhan me-)",
            "Belajar Berwirausaha (Wawancara)",
            "Menjadi Warga Dunia (Singkatan & Akronim)",
            "Cinta Indonesia (Huruf Kapital, Teks Pidato)"
        ],
        "Bahasa Inggris": [
            "What a delicious Bakso (Taste & Food)",
            "I want an ice cream (Quantifiers/Ordering)",
            "Comparison (Bigger, Smaller, Tallest)",
            "Parts of Body & Health Problems",
            "Clothes and Accessories",
            "Date and Month (Ordinal Numbers)"
        ]
    },
    "6 SD": {
        "Matematika": [
            "Operasi Hitung Campuran Bilangan Cacah",
            "Bilangan Bulat Negatif (Garis Bilangan & Operasi)",
            "Lingkaran (Unsur, Keliling, Luas)",
            "Bangun Ruang (Prisma, Tabung, Limas, Kerucut, Bola)",
            "Luas Permukaan dan Volume Bangun Ruang",
            "Statistika (Modus, Median, Mean)",
            "Peluang (Kejadian Pasti & Mustahil)"
        ],
        "IPA": [
            "Perkembangbiakan Tumbuhan (Generatif/Vegetatif)",
            "Perkembangbiakan Hewan (Ovipar, Vivipar, Ovovivipar)",
            "Adaptasi Makhluk Hidup dengan Lingkungan",
            "Komponen Listrik dan Rangkaian Seri/Paralel",
            "Sifat Magnet dan Cara Membuatnya",
            "Sistem Tata Surya (Planet, Rotasi, Revolusi)",
            "Gerhana Bulan dan Matahari"
        ],
        "Bahasa Indonesia": [
            "Bangga Menjadi Anak Indonesia (Teks Laporan)",
            "Musisi Indonesia di Pentas Dunia (Teks Eksplanasi)",
            "Taman Nasional (Formulir & Daftar Riwayat Hidup)",
            "Jeda untuk Iklim (Teks Pidato Persuasi)",
            "Anak-anak Mengubah Dunia (Surat Resmi/Pribadi)",
            "Karya Fiksi (Cerpen/Novel)"
        ],
        "Bahasa Inggris": [
            "I studied last night (Simple Past Tense)",
            "Holiday Experiences (Recount Text)",
            "Direction and Location (Map Reading)",
            "Government (President, Minister, etc.)",
            "Command and Request",
            "Future Plans (Will / Going to)"
        ]
    }
}

# --- 3. STYLE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&family=Roboto:wght@700&display=swap');
    
    h1 { font-family: 'Roboto', sans-serif !important; font-weight: 700; color: #1F1F1F; }
    .subtitle { font-family: 'Poppins', sans-serif !important; font-size: 18px; color: #555555; margin-top: -15px; margin-bottom: 25px; }
    
    .config-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-family: 'Poppins', sans-serif; font-weight: 600; }
    .footer-info { font-size: 13px; font-style: italic; color: #666; margin-top: 5px; border-top: 1px dashed #eee; padding-top: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI GENERATE WORD (DOCX) ---
def create_docx(data_soal, tipe, mapel, kelas, list_request):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)

    # Header Doc
    judul = doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    judul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_paragraph('_' * 70)

    # BAGIAN 1: SOAL
    doc.add_heading('A. SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        req_data = list_request[idx]
        topic_txt = req_data['topik']
        level_txt = req_data['level']

        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = True
        
        if tipe == "Pilihan Ganda":
            for op in item['opsi']:
                doc.add_paragraph(f"    {op}")
        else:
            doc.add_paragraph("\n" * 3) 

        # Footer Italic
        p_footer = doc.add_paragraph(f"Materi: {topic_txt} | Tingkat Kesulitan: {level_txt}")
        p_footer.italic = True
        p_footer.style.font.size = Pt(9)
        p_footer.style.font.color.rgb = RGBColor(100, 100, 100)
        doc.add_paragraph()

    # BAGIAN 2: KUNCI
    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN (Pegangan Guru)', level=1)
    
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

# --- 5. LOGIKA AI ---
def generate_soal_multi_granular(api_key, tipe_soal, kelas, mapel, list_request):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    req_str = ""
    for i, req in enumerate(list_request):
        req_str += f"- Soal No {i+1}: Topik '{req['topik']}' dengan Level '{req['level']}'\n"

    if tipe_soal == "Pilihan Ganda":
        json_structure = """[{"no":1,"soal":"...","opsi":["A.","B.","C.","D."],"kunci_index":0,"pembahasan":"..."}]"""
    else:
        json_structure = """[{"no":1,"soal":"...","poin_kunci":["..."],"pembahasan":"..."}]"""

    prompt = f"""
    Buatkan {len(list_request)} soal {tipe_soal} untuk siswa {kelas} SD Kurikulum Merdeka.
    Mata Pelajaran: {mapel}
    
    Instruksi Spesifik Per Soal:
    {req_str}
    
    Output WAJIB JSON Array:
    {json_structure}
    """
    
    try:
        response = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        if response.status_code != 200: return None, f"Error API: {response.text}"
        
        teks = response.json()['candidates'][0]['content']['parts'][0]['text']
        teks_bersih = teks.replace("```json", "").replace("```", "").strip()
        return json.loads(teks_bersih), None
    except Exception as e: return None, str(e)

# --- 6. SESSION STATE ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'tipe_aktif' not in st.session_state: st.session_state.tipe_aktif = None

# --- 7. SIDEBAR (PANEL GURU) ---
with st.sidebar:
    st.header("⚙️ Panel Guru")
    
    if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
    else: api_key = st.text_input("🔑 API Key", type="password")

    st.divider()
    
    # Pilih Kelas & Mapel (Global)
    kelas = st.selectbox("Kelas", [f"{i} SD" for i in range(1, 7)])
    mapel = st.selectbox("Mapel", ["Matematika", "IPA", "Bahasa Indonesia", "Bahasa Inggris"])
    
    st.divider()
    
    # Pilih Jumlah Soal
    jml_soal = st.selectbox("Jumlah Soal:", [1, 2, 3])
    
    list_request_user = [] 
    
    st.markdown("### 📝 Konfigurasi Per Soal")
    
    for i in range(jml_soal):
        with st.container():
            st.markdown(f"**Soal Nomor {i+1}**")
            
            # Cek Database Materi
            daftar_materi = DATABASE_MATERI.get(kelas, {}).get(mapel, [])
            
            if daftar_materi:
                topik_selected = st.selectbox(f"Materi Soal {i+1}", daftar_materi, key=f"topik_{i}")
            else:
                topik_selected = st.text_input(f"Materi Soal {i+1} (Manual)", key=f"topik_{i}")
                
            level_selected = st.selectbox(f"Level Soal {i+1}", ["Mudah", "Sedang", "Sulit (HOTS)"], key=f"lvl_{i}")
            
            list_request_user.append({"topik": topik_selected, "level": level_selected})
            st.markdown("---")

    if st.button("🗑️ Reset Konfigurasi"):
        st.session_state.hasil_soal = None
        st.rerun()

# --- 8. UI UTAMA ---
st.markdown("<h1>Generator Soal Sekolah Dasar (SD)</h1>", unsafe_allow_html=True)
st.markdown('<div class="subtitle">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)

tab_pg, tab_uraian = st.tabs(["📝 Pilihan Ganda", "✍️ Soal Uraian"])

# === TAB PILIHAN GANDA ===
with tab_pg:
    if st.button("🚀 Generate Soal PG", type="primary"):
        if not api_key: st.error("API Key belum diisi")
        else:
            with st.spinner("Sedang meracik soal sesuai pesanan..."):
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
                st.write(f"**{idx+1}. {item['soal']}**")
                ans = st.radio(f"Jawab {idx+1}", item['opsi'], key=f"rad_{idx}")
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                with st.expander("Kunci Jawaban"):
                    kunci = item['opsi'][item['kunci_index']]
                    if ans == kunci: st.success("Benar!")
                    else: st.error(f"Kunci: {kunci}")
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
                st.write(f"**Soal {idx+1}:** {item['soal']}")
                st.markdown(f"<div class='footer-info'>Materi: {info_req['topik']} | Kesulitan: {info_req['level']}</div>", unsafe_allow_html=True)
                st.text_area("Jawab:", height=80, key=f"essay_{idx}")
                with st.expander("Lihat Kunci Guru"):
                    st.write(item['pembahasan'])
