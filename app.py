import streamlit as st
import json
import requests
import os
import time
import matplotlib
# Backend Agg untuk stabilitas server
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from urllib.parse import quote
from docx import Document
from docx.shared import Inches
from openai import OpenAI

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Soal SD", page_icon="📚", layout="wide")

# --- 2. STYLE CSS (DIKUNCI TOTAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@700&family=Poppins:ital,wght@1,700&display=swap');
    .header-title { font-family: 'League Spartan', sans-serif; font-size: 32px; font-weight: bold; line-height: 1.2; color: #1E1E1E; }
    .header-sub { font-family: 'Poppins', sans-serif; font-size: 18px; font-weight: bold; font-style: italic; color: #444; margin-bottom: 5px; }
    .warning-text { font-size: 13px; color: #d9534f; font-weight: bold; margin-bottom: 20px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #e6f3ff 0%, #ffffff 100%); border-right: 1px solid #d1e3f3; }
    .stRadio [data-testid="stWidgetLabel"] p { font-weight: bold; font-size: 16px; color: #1E1E1E; }
    .metadata-text { font-size: 12px; font-style: italic; font-family: 'Poppins', sans-serif; font-weight: bold; color: #555; margin-top: 10px; margin-bottom: 15px;}
    div.stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE MATERI LENGKAP (DIKUNCI) ---
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

# --- 4. FUNGSI VISUAL AMAN ---
def render_accurate_chart(chart_data, title="Data Matematika"):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(8, 4))
    categories = [str(k) for k in chart_data.keys()]
    values = []
    for v in chart_data.values():
        try: values.append(float(v))
        except: values.append(0.0)
    
    bars = ax.bar(categories, values, color=plt.cm.Paired(range(len(categories))), edgecolor='black')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_ylabel("Jumlah/Nilai")
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f'{int(yval)}', ha='center', va='bottom', fontweight='bold')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    return buf

def construct_img_url(prompt):
    return f"https://image.pollinations.ai/prompt/{quote(prompt + ', high quality educational vector, white background')}?width=600&height=400&nologo=true&seed={int(time.time())}"

# --- 5. FUNGSI WORD ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item.get('soal','')}").bold = True
        if item.get('img_bytes'):
            doc.add_picture(BytesIO(item['img_bytes']), width=Inches(3.5))
        labels = ['A', 'B', 'C', 'D']
        opsi = item.get('opsi', [])
        for i, op in enumerate(opsi):
            prefix = f"{labels[i]}. "
            doc.add_paragraph(op if op.startswith(tuple(labels)) else f"{prefix}{op}")
        doc.add_paragraph(f"Materi : {item.get('materi','')} | Level : {item.get('level','')}")
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 6. SESSION STATE & SIDEBAR ---
if 'hasil_soal' not in st.session_state: st.session_state.hasil_soal = None
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

with st.sidebar:
    suffix = st.session_state.reset_counter
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.columns([1, 2, 1]); c2.image("logo.png", width=100)
    st.markdown("### ⚙️ Konfigurasi")
    api_key = st.secrets.get("OPENAI_API_KEY") or st.text_input("OpenAI API Key", type="password", key=f"api_{suffix}")
    if not api_key: st.stop()
    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()), key=f"k_{suffix}")
    mapel_sel = st.selectbox("Mata Pelajaran", list(DATABASE_MATERI[kelas_sel].keys()), key=f"m_{suffix}")
    jml_soal = st.slider("Jumlah Soal", 1, 5, 1, key=f"j_{suffix}")
    req_details = []
    any_img_selected = False
    for i in range(jml_soal):
        with st.expander(f"Soal {i+1}", expanded=(i==0)):
            top = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t_{i}_{suffix}")
            lvl = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], key=f"l_{i}_{suffix}")
            img_on = st.checkbox("Gunakan Gambar", value=False, key=f"img_{i}_{suffix}", disabled=any_img_selected)
            if img_on: any_img_selected = True
            req_details.append({"topik": top, "level": lvl, "use_image": img_on})
    c1, c2 = st.columns(2)
    btn_gen = c1.button("🚀 Generate", type="primary")
    if c2.button("🔄 Reset"):
        st.session_state.hasil_soal = None
        st.session_state.reset_counter += 1
        st.rerun()

# --- 7. MAIN PAGE ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.markdown('<div class="warning-text">⚠️ Batasan: Hanya 1 soal yang bisa menggunakan gambar/diagram per sesi agar akurasi tetap terjaga.</div>', unsafe_allow_html=True)
st.write("---")

if btn_gen:
    client = OpenAI(api_key=api_key)
    status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
    summary = "\n".join([f"- Soal {i+1}: {r['topik']} ({r['level']})" for i, r in enumerate(req_details)])
    
    # SYSTEM PROMPT DIPERBAIKI DENGAN KATA "json" (WAJIB)
    system_prompt = """Anda adalah Guru Matematika Senior & Pakar Evaluasi Kurikulum Merdeka Kemdikbud RI. 
    Tugas Anda adalah membuat soal bank soal SD. Anda wajib memberikan jawaban dalam format json.
    
    ATURAN KETAT:
    1. Jika materi terkait 'DATA' (Diagram Batang/Gambar/Lingkaran), Anda WAJIB memberikan key 'chart_data' { "Kategori": angka }.
    2. 'chart_data' harus berupa flat dictionary. Angka di soal HARUS sinkron dengan angka di chart_data.
    3. Output harus berupa objek json murni dengan key 'soal_list'.
    4. Seluruh teks wajib Bahasa Indonesia formal. Opsi A-D wajib diawali label A. B. C. D."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": f"Tolong buatkan soal dalam format json untuk Mapel: {mapel_sel}, Kelas: {kelas_sel}\n{summary}"}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content).get("soal_list", [])
        pb = st.progress(0)
        for i, item in enumerate(data):
            if i < len(req_details):
                item['materi'], item['level'] = req_details[i]['topik'], req_details[i]['level']
                item['img_bytes'] = None
                if req_details[i]['use_image']:
                    if item.get('chart_data'):
                        status_box.write(f"📊 Merender Grafik Akurat untuk {item['materi']}...")
                        item['img_bytes'] = render_accurate_chart(item['chart_data'], title=f"Visualisasi {item['materi']}").getvalue()
                    else:
                        status_box.write(f"🖼️ Menyiapkan Ilustrasi Edukatif...")
                        resp = requests.get(construct_img_url(item.get('image_prompt', 'educational illustration')))
                        if resp.status_code == 200: item['img_bytes'] = resp.content
            pb.progress(int(((i + 1) / len(data)) * 100))
        st.session_state.hasil_soal = data
        status_box.update(label="✅ Selesai!", state="complete", expanded=False)
    except Exception as e: 
        status_box.update(label="❌ Terjadi kesalahan", state="error")
        st.error(f"Gagal: {e}")

# --- 8. TAMPILAN HASIL (DIKUNCI) ---
if st.session_state.hasil_soal:
    st.download_button("📥 Download Word", create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel), f"Soal_{mapel_sel}.docx")
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            st.markdown(f"### Soal {idx+1}\n**{item.get('soal','')}**")
            if item.get('img_bytes'): st.image(item['img_bytes'], width=500)
            labels = ['A', 'B', 'C', 'D']
            opsi = item.get('opsi', [])
            clean_opsi = [o if o.startswith(labels[i]) else f"{labels[i]}. {o}" for i, o in enumerate(opsi)]
            pilih = st.radio("Pilih Jawaban:", clean_opsi, key=f"ans_{idx}_{suffix}", index=None)
            st.markdown(f"<div class='metadata-text'>Materi : {item.get('materi','')} | Level : {item.get('level','')}</div>", unsafe_allow_html=True)
            if pilih:
                if clean_opsi.index(pilih) == item.get('kunci_index', 0): st.success("✅ Jawaban Anda Benar!")
                else: st.error("❌ Jawaban Anda Salah.")
            with st.expander("Kunci & Pembahasan"): st.write(item.get('pembahasan',''))

st.write("---")
st.markdown("<div style='text-align: center; font-size: 12px;'><b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital \"Akademi Pelajar\"</p><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p><p>Semua hak cipta dilindungi undang-undang</p></b></div>", unsafe_allow_html=True)
