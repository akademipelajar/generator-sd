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
    .header-title { font-family: 'League Spartan', sans-serif; font-size: 32px; font-weight: bold; line-height: 1.2; color: #1E1E1E; }
    .header-sub { font-family: 'Poppins', sans-serif; font-size: 18px; font-weight: bold; font-style: italic; color: #444; margin-bottom: 5px; }
    .warning-text { font-size: 13px; color: #d9534f; font-weight: bold; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #e6f3ff 0%, #ffffff 100%); border-right: 1px solid #d1e3f3; }
    .stRadio [data-testid="stWidgetLabel"] p, .stCheckbox p { font-weight: bold; font-size: 16px; color: #1E1E1E; }
    .metadata-text { font-size: 12px; font-style: italic; font-family: 'Poppins', sans-serif; font-weight: bold; color: #555; margin-top: 10px; margin-bottom: 15px;}
    div.stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE MATERI LENGKAP (DIKUNCI TOTAL) ---
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

# --- 4. FUNGSI WORD (FORMAT MULTI-BENTUK & DETAIL PEMBAHASAN) ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_heading('A. DAFTAR SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. [{item.get('bentuk', '')}] {item.get('soal','')}\n").bold = True
        
        bentuk = item.get('bentuk')
        if bentuk == "PG Sederhana":
            for op in item.get('opsi', []): doc.add_paragraph(op, style='List Bullet')
        elif bentuk == "PG Kompleks":
            doc.add_paragraph("(Pilih beberapa jawaban yang benar)")
            for op in item.get('opsi', []): doc.add_paragraph(f"☐ {op}")
        elif bentuk == "PG Kompleks Kategori":
            for kat in item.get('kategori_pernyataan', []):
                doc.add_paragraph(f"• {kat['pernyataan']} (...........)")
        elif bentuk == "Uraian":
            doc.add_paragraph("Jawaban: ............................................................................................")
            
        meta = doc.add_paragraph(f"Materi : {item.get('materi','')} | Level : {item.get('level','')}")
        meta.italic = True
        doc.add_paragraph("")

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN & PEMBAHASAN DETAIL', level=1)
    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"Nomor {idx+1}:").bold = True
        doc.add_paragraph(f"Bentuk: {item.get('bentuk', '')}")
        
        # Kunci Jawaban
        kunci = item.get('kunci_jawaban_teks', '')
        doc.add_paragraph(f"KUNCI: {kunci}").bold = False
        
        # Pembahasan Langkah demi Langkah
        doc.add_paragraph("PEMBAHASAN:").bold = True
        pembahasan_list = item.get('pembahasan_langkah', [])
        for step in pembahasan_list:
            doc.add_paragraph(f"- {step}")
            
        doc.add_paragraph("-" * 30)
        
    bio = BytesIO(); doc.save(bio); bio.seek(0); return bio

# --- 5. SESSION STATE & SIDEBAR (DIKUNCI) ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

with st.sidebar:
    suffix = st.session_state.reset_counter
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1]); c2.image("logo.png", width=100)
    st.markdown("### ⚙️ Konfigurasi")
    api_key = st.secrets.get("OPENAI_API_KEY") or st.text_input("OpenAI API Key", type="password", key=f"api_{suffix}")
    if not api_key: st.info("💡 Masukkan API Key di sidebar untuk memulai."); st.stop()
    
    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()), key=f"k_{suffix}")
    mapel_sel = st.selectbox("Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()), key=f"m_{suffix}")
    jml_soal = st.slider("Jumlah Soal (Max 10)", 1, 10, 2, key=f"j_{suffix}")
    
    req_details = []
    for i in range(jml_soal):
        with st.expander(f"Konfigurasi Soal {i+1}", expanded=(i==0)):
            top = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t_{i}_{suffix}")
            lvl = st.selectbox("Level", ["Mudah", "Sedang", "Sulit (HOTS)"], key=f"l_{i}_{suffix}")
            fmt = st.selectbox("Bentuk Soal", ["PG Sederhana", "PG Kompleks", "PG Kompleks Kategori", "Uraian"], key=f"f_{i}_{suffix}")
            req_details.append({"topik": top, "level": lvl, "bentuk": fmt})
            
    c1, c2 = st.columns(2)
    btn_gen = c1.button("🚀 Generate", type="primary")
    if c2.button("🔄 Reset"):
        st.session_state.hasil_soal = None; st.session_state.reset_counter += 1; st.rerun()

# --- 6. MAIN PAGE HEADER ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.write("---")

# --- 7. PERSONA MASTER & LOGIKA PEMBAHASAN (AKUMULATIF) ---
if btn_gen:
    client = OpenAI(api_key=api_key)
    status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
    summary = "\n".join([f"- Soal {i+1}: {r['topik']}, Level: {r['level']}, Bentuk: {r['bentuk']}" for i, r in enumerate(req_details)])
    
    # PERSONA DIKUNCI & DIPERTAJAM UNTUK PEMBAHASAN
    system_prompt = """Anda adalah Pakar Pengembang Kurikulum Merdeka Kemdikbud RI dan Penulis Bank Soal Profesional. 
    Wajib memberikan jawaban dalam format json murni.

    KARAKTERISTIK SOAL HOTS (Level Sulit):
    - Mengukur kognitif tinggi: Menganalisis, mengevaluasi, menciptakan.
    - Kontekstual: Menggunakan narasi dunia nyata/kasus sehari-hari anak Indonesia.
    - Stimulus: Gunakan informasi yang menuntut murid berpikir kritis sebelum menjawab.

    ATURAN PEMBAHASAN:
    - Wajib mendalam dan langkah demi langkah (Step-by-Step).
    - Susun pembahasan sebagai list/array teks yang logis (bukan paragraf panjang).

    JSON STRUCTURE:
    {
      "soal_list": [
        {
          "no": 1,
          "soal": "...",
          "bentuk": "...",
          "materi": "...",
          "level": "...",
          "kunci_jawaban_teks": "Ringkasan kunci jawaban",
          "pembahasan_langkah": ["Langkah 1: ...", "Langkah 2: ...", "Langkah 3: ..."],
          "opsi": ["A...", "B...", "C...", "D..."],
          "kategori_pernyataan": [{"pernyataan": "...", "kunci": "Benar/Salah"}]
        }
      ]
    }"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Buat json soal SD Kurikulum Merdeka sesuai rincian:\n{summary}"}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content).get("soal_list", [])
        st.session_state.hasil_soal = data
        status_box.update(label="✅ Soal Berhasil Dibuat!", state="complete", expanded=False)
    except Exception as e: st.error(f"Gagal: {e}")

# --- 8. TAMPILAN HASIL (LOCKED UI) ---
if st.session_state.hasil_soal:
    st.download_button("📥 Download Word", create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel), f"Soal_Master_{mapel_sel}.docx")
    
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            st.markdown(f"### Soal {idx+1} ({item.get('bentuk', '')})")
            st.markdown(f"**{item.get('soal','')}**")
            
            bentuk = item.get('bentuk')
            if bentuk == "PG Sederhana":
                st.radio("Pilih jawaban:", item.get('opsi', []), key=f"ans_{idx}_{suffix}", index=None)
            elif bentuk == "PG Kompleks":
                for o_idx, opt in enumerate(item.get('opsi', [])):
                    st.checkbox(opt, key=f"chk_{idx}_{o_idx}_{suffix}")
            elif bentuk == "PG Kompleks Kategori":
                for k_idx, kat in enumerate(item.get('kategori_pernyataan', [])):
                    st.radio(f"Pernyataan: {kat['pernyataan']}", ["Benar", "Salah"], key=f"kat_{idx}_{k_idx}_{suffix}", horizontal=True, index=None)
            elif bentuk == "Uraian":
                st.text_area("Tuliskan jawaban:", key=f"txt_{idx}_{suffix}")

            # METADATA DIKUNCI (Bold & Italic)
            st.markdown(f"<div class='metadata-text'>Materi : {item.get('materi','')} | Level : {item.get('level','')}</div>", unsafe_allow_html=True)
            
            with st.expander("Lihat Kunci & Pembahasan Langkah demi Langkah"):
                # Menampilkan kunci khusus untuk kategori
                if bentuk == "PG Kompleks Kategori":
                    st.markdown("**Kunci Pernyataan:**")
                    for kat in item.get('kategori_pernyataan', []):
                        st.write(f"- {kat['pernyataan']}: **{kat['kunci']}**")
                else:
                    st.success(f"**Kunci Jawaban:** {item.get('kunci_jawaban_teks','')}")
                
                st.markdown("**Pembahasan:**")
                for step in item.get('pembahasan_langkah', []):
                    st.write(f"✅ {step}")

# --- 9. FOOTER (DIKUNCI TOTAL) ---
st.write("---")
st.markdown("""
<div style='text-align: center; font-size: 12px;'>
    <b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital "Akademi Pelajar"</p></b>
    <b><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p></b>
    <b><p>Semua hak cipta dilindungi undang-undang</p></b>
</div>
""", unsafe_allow_html=True)
