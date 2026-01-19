import streamlit as st
import json
import requests
import os
import time
import matplotlib
# Backend Agg untuk stabilitas server Streamlit
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from urllib.parse import quote
from docx import Document
from docx.shared import Inches, Pt
from openai import OpenAI

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Soal SD", page_icon="📚", layout="wide")

# --- 2. STYLE CSS (DIKUNCI TOTAL: Font, Header, Sidebar, Metadata) ---
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

# --- 4. FUNGSI VISUAL (PERBAIKAN: GEOMETRY ENGINE) ---
def render_geometry(geo_data, title="Visualisasi Bangun Ruang"):
    """Menggambar Kubus/Balok secara matematis agar 100% akurat"""
    plt.close('all')
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, projection='3d')
    
    p = float(geo_data.get('p', 5))
    l = float(geo_data.get('l', 5))
    t = float(geo_data.get('t', 5))
    
    # Koordinat titik sudut
    x = [0, p, p, 0, 0, p, p, 0]
    y = [0, 0, l, l, 0, 0, l, l]
    z = [0, 0, 0, 0, t, t, t, t]
    
    # Garis pembentuk rangka
    connections = [[0,1,2,3,0], [4,5,6,7,4], [0,4], [1,5], [2,6], [3,7]]
    for conn in connections:
        ax.plot([x[i] for i in conn], [y[i] for i in conn], [z[i] for i in conn], color='blue', linewidth=2)
    
    # Tambahkan Label Angka Akurat
    ax.text(p/2, -0.5, 0, f"{int(p)} cm", color='red', fontweight='bold')
    ax.text(p + 0.5, l/2, 0, f"{int(l)} cm", color='green', fontweight='bold')
    ax.text(-0.5, 0, t/2, f"{int(t)} cm", color='purple', fontweight='bold')
    
    ax.set_axis_off()
    plt.title(title, pad=20, fontsize=12, fontweight='bold')
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    return buf

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

def safe_download_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200: return BytesIO(resp.content)
    except: return None
    return None

# --- 5. FUNGSI EKSTRAKSI OPSI (VALIDATOR OPSI A-D) ---
def get_clean_options(item):
    opsi_raw = item.get('opsi') or item.get('pilihan') or item.get('options') or item.get('choices') or []
    labels = ['A', 'B', 'C', 'D']
    clean = []
    for i, text in enumerate(opsi_raw):
        if i >= 4: break
        t = str(text).strip()
        if t and not t.startswith(tuple(labels)):
            t = f"{labels[i]}. {t}"
        elif not t:
            t = f"{labels[i]}. [Kosong]"
        clean.append(t)
    while len(clean) < 4:
        clean.append(f"{labels[len(clean)]}. [Pilihan tidak tersedia]")
    return clean

# --- 6. FUNGSI WORD (SOAL + KUNCI LENGKAP) ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')
    
    # BAGIAN A: SOAL
    doc.add_heading('A. SOAL PILIHAN GANDA', level=1)
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item.get('soal','')}").bold = True
        if item.get('img_bytes'):
            doc.add_picture(BytesIO(item['img_bytes']), width=Inches(3.5))
        clean_opsi = get_clean_options(item)
        for op in clean_opsi:
            doc.add_paragraph(op)
        meta = doc.add_paragraph(f"Materi : {item.get('materi','')} | Level : {item.get('level','')}")
        meta.italic = True
        doc.add_paragraph("")

    # BAGIAN B: KUNCI (HALAMAN BARU)
    doc.add_page_break()
    doc.add_heading('B. KUNCI JAWABAN & PEMBAHASAN', level=1)
    for idx, item in enumerate(data_soal):
        c_opsi = get_clean_options(item)
        k_idx = item.get('kunci_index', 0)
        k_teks = c_opsi[k_idx] if k_idx < len(c_opsi) else "N/A"
        pk = doc.add_paragraph()
        pk.add_run(f"Nomor {idx+1}: ").bold = True
        pk.add_run(f"Jawaban {k_teks}")
        pp = doc.add_paragraph()
        pp.add_run("Pembahasan: ").italic = True
        pp.add_run(item.get('pembahasan', 'Tidak ada pembahasan.'))
        doc.add_paragraph("-" * 30)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 7. SESSION STATE & SIDEBAR ---
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
        st.session_state.reset_counter += 1 # Perbaikan logika reset sidebar
        st.rerun()

# --- 8. MAIN PAGE ---
st.markdown('<div class="header-title">Generator Soal SD</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Berdasarkan Kurikulum Merdeka</div>', unsafe_allow_html=True)
st.markdown('<div class="warning-text">⚠️ Batasan: Hanya 1 soal yang bisa menggunakan gambar/diagram per sesi agar akurasi tetap terjaga.</div>', unsafe_allow_html=True)
st.write("---")

if btn_gen:
    client = OpenAI(api_key=api_key)
    status_box = st.status("✅ Soal Dalam Proses Pembuatan, Silahkan Ditunggu.", expanded=True)
    summary = "\n".join([f"- Soal {i+1}: {r['topik']} ({r['level']})" for i, r in enumerate(req_details)])
    
    # PERSONA DIPERTAJAM UNTUK GEOMETRI AKURAT
    system_prompt = """Anda adalah Guru Matematika Senior & Pakar Evaluasi Kurikulum Merdeka Kemdikbud RI. 
    Wajib memberikan jawaban dalam format json murni.
    TUGAS AKURASI TINGGI:
    1. Jika materi diagram, wajib sertakan 'chart_data' { "Kategori": angka }.
    2. Jika materi Bangun Ruang (Volume/Luas), wajib sertakan 'geometry_data' { "type": "kubus", "p": angka, "l": angka, "t": angka }.
    3. Angka di soal HARUS sama dengan angka di data visual."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": f"Buat json soal SD untuk: {mapel_sel}, Kelas: {kelas_sel}\n{summary}"}
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
                    # LOGIKA HYBRID: Cek Diagram atau Geometri atau Ilustrasi
                    if item.get('geometry_data'):
                        status_box.write(f"📐 Merender Sketsa Geometri Akurat untuk {item['materi']}...")
                        item['img_bytes'] = render_geometry(item['geometry_data'], title=f"Visualisasi {item['materi']}").getvalue()
                    elif item.get('chart_data'):
                        status_box.write(f"📊 Merender Diagram Akurat...")
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

# --- 9. TAMPILAN HASIL (DIKUNCI) ---
if st.session_state.hasil_soal:
    st.download_button("📥 Download Word", create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel), f"Soal_{mapel_sel}.docx")
    for idx, item in enumerate(st.session_state.hasil_soal):
        with st.container(border=True):
            st.markdown(f"### Soal {idx+1}\n**{item.get('soal','')}**")
            if item.get('img_bytes'): st.image(item['img_bytes'], width=500)
            clean_opsi = get_clean_options(item)
            pilih = st.radio("Pilih Jawaban:", clean_opsi, key=f"ans_{idx}_{suffix}", index=None)
            st.markdown(f"<div class='metadata-text'>Materi : {item.get('materi','')} | Level : {item.get('level','')}</div>", unsafe_allow_html=True)
            if pilih:
                if clean_opsi.index(pilih) == item.get('kunci_index', 0): st.success("✅ Jawaban Anda Benar!")
                else: st.error("❌ Jawaban Anda Salah.")
            with st.expander("Kunci & Pembahasan"): 
                st.info(f"Kunci: {clean_opsi[item.get('kunci_index', 0)]}")
                st.write(item.get('pembahasan',''))

st.write("---")
st.markdown("<div style='text-align: center; font-size: 12px;'><b><p>Aplikasi Generator Soal ini Milik Bimbingan Belajar Digital \"Akademi Pelajar\"</p><p>Dilarang menyebarluaskan tanpa persetujuan tertulis dari Akademi Pelajar</p><p>Semua hak cipta dilindungi undang-undang</p></b></div>", unsafe_allow_html=True)
