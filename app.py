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

# --- 4. MAPPING LABEL KETERANGAN SOAL (LOCKED) ---
LABEL_BENTUK = {
    "PG Sederhana": "Pilihlah satu jawaban yang benar",
    "PG Kompleks": "Pilihlah lebih dari satu jawaban yang benar",
    "PG Kompleks Kategori": "Pilih Benar atau Salah dari tiap pernyataan ini",
    "Uraian": "Jawablah pertanyaan berikut dengan tepat"
}

# --- 5. FUNGSI EKSTRAKSI OPSI ---
def get_clean_options(item):
    opsi_raw = item.get('opsi') or []
    labels = ['A', 'B', 'C', 'D']
    clean = []
    for i, text in enumerate(opsi_raw):
        if i >= 4: break
        t = str(text).strip()
        if t and not t.startswith(tuple(labels)): t = f"{labels[i]}. {t}"
        clean.append(t if t else f"{labels[i]}. [Kosong]")
    while len(clean) < 4: clean.append(f"{labels[len(clean)]}. [N/A]")
    return clean

# --- 6. FUNGSI WORD (DIKUNCI: TERMASUK KUNCI PER PERNYATAAN) ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    doc.add_heading('A. DAFTAR SOAL', level=1)
    
    for idx, item in enumerate(data_soal):
        bentuk = item.get('bentuk', '')
        keterangan = LABEL_BENTUK.get(bentuk, "")
        p = doc.add_paragraph()
        p.add_run(f"Soal {idx+1} ({keterangan})").italic = True
        
        doc.add_paragraph(item.get('soal',''), style='Normal').bold = True
        
        if bentuk == "PG Sederhana":
            for op in get_clean_options(item): doc.add_paragraph(op)
        elif bentuk == "PG Kompleks":
            for op in get_clean_options(item): doc.add_paragraph(f"☐ {op}")
        elif bentuk == "PG Kompleks Kategori":
            for kat in item.get('kategori_pernyataan', []):
                doc.add_paragraph(f"• {kat['pernyataan']} (...........)")
        elif bentuk == "Uraian":
            doc.add_paragraph("Jawaban: ...................................................................")
            
        doc.add_paragraph(f"Materi : {item.get('materi','')} | Level : {item.get('level','')}")
        doc.add_paragraph("")

    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN & PEMBAHASAN', level=1)
    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"Nomor {idx+1}:").bold = True
        
        if item.get('bentuk') == "PG Kompleks Kategori":
            doc.add_paragraph("KUNCI PER PERNYATAAN:")
            for kat in item.get('kategori_pernyataan', []):
                doc.add_paragraph(f"- {kat['pernyataan']}: {kat['kunci']}")
        else:
            doc.add_paragraph(f"KUNCI: {item.get('kunci_jawaban_teks', '')}")
            
        doc.add_paragraph("PEMBAHASAN LANGKAH DEMI LANGKAH:")
        for step in item.get('pembahasan_langkah', []):
            doc.add_paragraph(f"• {step}")
        doc.add_paragraph("-" * 20)
        
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
    if not api_key: st.info("💡 Masukkan API Key untuk memulai."); st.stop()
    
    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()), key=f"k_{suffix}")
    mapel_sel = st.selectbox("Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()), key=f"m_{suffix}")
    jml_soal = st.slider("Jumlah Soal (Max 10)", 1, 10, 2, key=f"j_{suffix}")
    
    req_details = []
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=(i==0)):
            top = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t_{i}_{suffix}")
            lvl = st.selectbox("Level", ["Mudah", "Sedang", "Sulit (HOTS)"], key=f"l_{i}_{suffix}")
            fmt = st.selectbox("Bentuk Soal", list(LABEL_BENTUK.keys()), key=f"f_{i}_{suffix}")
            req_details.append({"topik": top, "level": lvl, "bentuk": fmt})
            
    c1, c2 = st.columns(2)
    btn_gen = c1.button("🚀 Generate", type="primary")
    if c2.button("🔄 Reset"):
        st.session_state.hasil_soal = None; st.session_state.reset_counter += 1; st.rerun()

# --- 8. MAIN PAGE HEADER ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.write("---")

# --- 9. PERSONA & LOGIKA JANTUNG (LOCKED & CUMULATIVE) ---
if btn_gen:
    client = OpenAI(api_key=api_key)
    status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
    summary = "\n".join([f"- Soal {i+1}: {r['topik']}, Level: {r['level']}, Bentuk: {r['bentuk']}" for i, r in enumerate(req_details)])
    
    system_prompt = """Anda adalah Pakar Pengembang Kurikulum Merdeka Kemdikbud RI dan Penulis Bank Soal Profesional. 
    Wajib memberikan jawaban dalam format json murni.

    KARAKTERISTIK SOAL HOTS:
    - Kognitif Tinggi: Menganalisis, mengevaluasi, menciptakan. Bukan hafalan.
    - Berpikir Kritis: Mencari kaitan informasi dan mengambil keputusan.
    - Kontekstual: Menggunakan stimulus kompleks (kasus/tabel/narasi panjang) dunia nyata.

    ATURAN KETAT BENTUK SOAL:
    1. PG Kompleks: Jawaban benar HARUS berjumlah 2, 3, atau semua (4 benar). Jawaban wajib saling berkorelasi kuat dengan pertanyaan.
    2. PG Kompleks Kategori: Pernyataan HARUS berkorelasi langsung dengan stimulus/pertanyaan.
    
    ATURAN PEMBAHASAN:
    - Wajib detail, langkah demi langkah, disusun ke bawah (array of strings).
    - Khusus Kategori: Wajib jelaskan alasan spesifik mengapa pernyataan itu Benar atau Salah secara logis.

    JSON STRUCTURE:
    {
      "soal_list": [
        {
          "no": 1, "soal": "...", "bentuk": "...", "materi": "...", "level": "...",
          "kunci_jawaban_teks": "...",
          "pembahasan_langkah": ["Langkah 1: ...", "Langkah 2: ..."],
          "opsi": ["A...", "B...", "C...", "D..."],
          "kategori_pernyataan": [{"pernyataan": "...", "kunci": "Benar/Salah", "alasan": "..."}]
        }
      ]
    }"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Buat json soal SD Kurikulum Merdeka:\n{summary}"}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content).get("soal_list", [])
        st.session_state.hasil_soal = data
        status_box.update(label="✅ Soal Berhasil Dibuat!", state="complete", expanded=False)
    except Exception as e: st.error(f"Gagal: {e}")

# --- 10. TAMPILAN HASIL (LOCKED UI) ---
if st.session_state.hasil_soal:
    st.download_button("📥 Download Word", create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel), f"Bank_Soal_AKM_{mapel_sel}.docx")
    
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            bentuk = item.get('bentuk')
            keterangan = LABEL_BENTUK.get(bentuk, "")
            st.markdown(f"#### Soal {idx+1} *({keterangan})*")
            st.markdown(f"**{item.get('soal','')}**")
            
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

            st.markdown(f"<div class='metadata-text'>Materi : {item.get('materi','')} | Level : {item.get('level','')}</div>", unsafe_allow_html=True)
            
            with st.expander("Lihat Kunci & Pembahasan Mendalam"):
                if bentuk == "PG Kompleks Kategori":
                    st.markdown("**Analisis Pernyataan:**")
                    for kat in item.get('kategori_pernyataan', []):
                        st.write(f"• {kat['pernyataan']} → **{kat['kunci']}**")
                        st.caption(f"Alasan: {kat.get('alasan','')}")
                else:
                    st.success(f"**Kunci:** {item.get('kunci_jawaban_teks','')}")
                
                st.markdown("**Langkah Pembahasan:**")
                for step in item.get('pembahasan_langkah', []):
                    st.write(f"✅ {step}")

# --- 11. FOOTER (DIKUNCI TOTAL) ---
st.write("---")
st.markdown("<div style='text-align: center; font-size: 12px;'><b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital \"Akademi Pelajar\"</p><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p><p>Semua hak cipta dilindungi undang-undang</p></b></div>", unsafe_allow_html=True)
