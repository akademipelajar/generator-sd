import streamlit as st
import json
import os
import time
from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt
from openai import OpenAI

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Soal SD", page_icon="📚", layout="wide")

# --- 2. STYLE CSS (DIKUNCI TOTAL: Font, Header, Sidebar Gradient, Metadata) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');
    
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
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #e6f3ff 0%, #ffffff 100%); 
        border-right: 1px solid #d1e3f3; 
    }
    .stRadio [data-testid="stWidgetLabel"] p { 
        font-weight: bold; 
        font-size: 16px; 
        color: #1E1E1E; 
    }
    .metadata-text { 
        font-size: 12px; 
        font-style: italic; 
        font-family: 'Poppins', sans-serif; 
        font-weight: bold; 
        color: #555; 
        margin-top: 10px; 
        margin-bottom: 15px;
    }
    div.stButton > button { 
        width: 100%; 
    }
</style>
""", unsafe_allow_html=True)

# --- 3. TAMPILAN HEADER (DIKUNCI DI ATAS AGAR ANTI-BLANK) ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.write("---")

# --- 4. DATABASE MATERI LENGKAP (DIKUNCI) ---
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

# --- 5. FUNGSI EKSTRAKSI OPSI ---
def get_clean_options(item):
    opsi_raw = item.get('opsi') or item.get('pilihan') or item.get('options') or []
    labels = ['A', 'B', 'C', 'D']
    clean = []
    for i, text in enumerate(opsi_raw):
        if i >= 4: break
        t = str(text).strip()
        if t and not t.startswith(tuple(labels)): t = f"{labels[i]}. {t}"
        clean.append(t if t else f"{labels[i]}. [Kosong]")
    while len(clean) < 4: clean.append(f"{labels[len(clean)]}. [N/A]")
    return clean

# --- 6. FUNGSI GENERATE WORD ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_heading('A. SOAL PILIHAN GANDA', level=1)
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph(); p.add_run(f"{idx+1}. {item.get('soal','')}").bold = True
        for op in get_clean_options(item): doc.add_paragraph(op)
        meta = doc.add_paragraph(f"Materi : {item.get('materi','')} | Level : {item.get('level','')}"); meta.italic = True
        doc.add_paragraph("")
    doc.add_page_break(); doc.add_heading('B. KUNCI JAWABAN & PEMBAHASAN', level=1)
    for idx, item in enumerate(data_soal):
        c_opsi = get_clean_options(item); k_idx = item.get('kunci_index', 0)
        pk = doc.add_paragraph(); pk.add_run(f"Nomor {idx+1}: ").bold = True
        pk.add_run(f"Jawaban {c_opsi[k_idx] if k_idx < 4 else 'N/A'}")
        doc.add_paragraph(f"Pembahasan: {item.get('pembahasan','')}")
    bio = BytesIO(); doc.save(bio); bio.seek(0); return bio

# --- 7. SESSION STATE & SIDEBAR (DIKUNCI) ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

with st.sidebar:
    suffix = st.session_state.reset_counter
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1]); c2.image("logo.png", width=100)
    
    st.markdown("### ⚙️ Konfigurasi")
    api_key = st.secrets.get("OPENAI_API_KEY") or st.text_input("OpenAI API Key", type="password", key=f"api_{suffix}")
    
    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()), key=f"k_{suffix}")
    mapel_sel = st.selectbox("Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()), key=f"m_{suffix}")
    jml_soal = st.slider("Jumlah Soal", 1, 10, 2, key=f"j_{suffix}")
    
    req_details = []
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=(i==0)):
            top = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t_{i}_{suffix}")
            lvl = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], key=f"l_{i}_{suffix}")
            req_details.append({"topik": top, "level": lvl})
            
    c1, c2 = st.columns(2)
    btn_gen = c1.button("🚀 Generate", type="primary")
    if c2.button("🔄 Reset"):
        st.session_state.hasil_soal = None
        st.session_state.reset_counter += 1
        st.rerun()

# --- 8. JANTUNG LOGIKA (MASTER PERSONA - NO IMAGES) ---
if btn_gen:
    if not api_key:
        st.warning("⚠️ Masukkan API Key di sidebar untuk memulai.")
    else:
        client = OpenAI(api_key=api_key)
        status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
        summary = "\n".join([f"- Soal {i+1}: {r['topik']} ({r['level']})" for i, r in enumerate(req_details)])
        
        system_prompt = """Anda adalah Pakar Pengembang Kurikulum Merdeka Kemdikbud RI dan Penulis Bank Soal Profesional. 
        Wajib memberikan jawaban dalam format json murni.

        ATURAN KETAT PERSONA & KONTEN:
        1. BAHASA: Wajib 100% Bahasa Indonesia formal sesuai tingkat kognitif anak SD (Fase A/B/C).
        2. FORMAT OPSI: Wajib 4 pilihan (A-D) yang logis, mengecoh, dan relevan.
        3. PENDEKATAN: Gunakan konteks kehidupan nyata Indonesia. Untuk level 'Sulit', wajib soal analisis (HOTS).
        4. SINKRONISASI: Pastikan soal sesuai dengan Topik dan Level yang diminta.
        5. JSON STRUCTURE: Key utama 'soal_list' berisi 'soal', 'opsi' (array 4 string), 'kunci_index' (0-3), 'pembahasan'."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Buat json soal SD Kurikulum Merdeka: {mapel_sel}, Kelas: {kelas_sel}\n{summary}"}],
                response_format={"type": "json_object"}
            )
            raw_res = json.loads(response.choices[0].message.content)
            data = raw_res.get("soal_list") or raw_res.get("questions") or []
            if not data and isinstance(raw_res, list): data = raw_res
            
            for i, item in enumerate(data):
                if i < len(req_details):
                    item['materi'], item['level'] = req_details[i]['topik'], req_details[i]['level']
            
            st.session_state.hasil_soal = data
            status_box.update(label="✅ Selesai!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# --- 9. TAMPILAN HASIL (LOCKED) ---
if st.session_state.hasil_soal:
    st.download_button("📥 Download Word", create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel), f"Soal_{mapel_sel}.docx")
    for idx, item in enumerate(st.session_state.hasil_soal):
        if not isinstance(item, dict): continue
        with st.container(border=True):
            st.markdown(f"### Soal {idx+1}\n**{item.get('soal','')}**")
            c_opsi = get_clean_options(item)
            pilih = st.radio("Pilih Jawaban:", c_opsi, key=f"ans_{idx}_{suffix}", index=None)
            st.markdown(f"<div class='metadata-text'>Materi : {item.get('materi','')} | Level : {item.get('level','')}</div>", unsafe_allow_html=True)
            if pilih and c_opsi.index(pilih) == item.get('kunci_index', 0): st.success("✅ Benar!")
            elif pilih: st.error("❌ Salah.")
            with st.expander("Kunci & Pembahasan"): st.write(item.get('pembahasan',''))

# --- 10. FOOTER (DIKUNCI TOTAL) ---
st.write("---")
st.markdown("<div style='text-align: center; font-size: 12px;'><b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital \"Akademi Pelajar\"</p><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p><p>Semua hak cipta dilindungi undang-undang</p></b></div>", unsafe_allow_html=True)
