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
    page_title="Generator Soal SD - Akademi Pelajar",
    page_icon="📚",
    layout="wide"
)

# --- KONFIGURASI MODEL OPENAI ---
TEXT_MODEL = "gpt-4o-mini"

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

# --- 4. FUNGSI GENERATE GAMBAR (DENGAN HEADERS BROWSER) ---
def fetch_image(prompt_text):
    """Mengambil gambar dari Pollinations AI dengan penanganan error yang kuat."""
    if not prompt_text or prompt_text.strip() == "":
        return None
        
    # Tambahkan gaya agar seragam (Kartun Pendidikan)
    full_prompt = f"{prompt_text}, simple cartoon vector style, educational illustration, white background, high quality"
    encoded_prompt = quote(full_prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=512&height=512&seed=99&nologo=true"
    
    # Headers agar tidak dianggap bot oleh server
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            # Pastikan kontennya memang gambar
            if "image" in response.headers.get("Content-Type", "").lower():
                return BytesIO(response.content)
        return None
    except Exception as e:
        print(f"Gagal mengambil gambar: {e}")
        return None

# --- 5. FUNGSI GENERATE WORD ---
def create_docx(data_soal, mapel, kelas):
    doc = Document()
    doc.add_heading(f'LATIHAN SOAL {mapel.upper()}', 0)
    doc.add_paragraph(f'Kelas: {kelas}')

    doc.add_heading('A. SOAL PILIHAN GANDA', level=1)
    
    for idx, item in enumerate(data_soal):
        p = doc.add_paragraph()
        p.add_run(f"{idx+1}. {item['soal']}").bold = False
        
        # Masukkan gambar jika ada
        if item.get('image_bytes'):
            try:
                img_stream = BytesIO(item['image_bytes']) # Buat stream baru agar pointer di awal
                doc.add_picture(img_stream, width=Inches(2.5))
            except:
                doc.add_paragraph("[Gambar tidak dapat dimuat]")
        
        for op in item['opsi']:
            doc.add_paragraph(op, style='List Bullet')

    doc.add_page_break()
    doc.add_heading('B. KUNCI & PEMBAHASAN', level=1)
    for idx, item in enumerate(data_soal):
        doc.add_paragraph(f"No {idx+1}: {item['opsi'][item['kunci_index']]}")
        doc.add_paragraph(f"Pembahasan: {item['pembahasan']}")
        doc.add_paragraph("-" * 15)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 6. LOGIKA AI OPENAI ---
def generate_all_data(api_key, kelas, mapel, list_request):
    client = OpenAI(api_key=api_key)

    req_str = ""
    for i, req in enumerate(list_request):
        req_str += f"- Soal {i+1}: Materi '{req['topik']}', Level '{req['level']}', Pakai Gambar? {'Ya' if req['use_image'] else 'Tidak'}\n"

    prompt = f"""
    Buatkan {len(list_request)} soal pilihan ganda SD kelas {kelas}. 
    Mapel: {mapel}.
    Detail: {req_str}

    Output harus JSON murni:
    [
      {{
        "no": 1,
        "soal": "pertanyaan",
        "opsi": ["A...", "B...", "C...", "D..."],
        "kunci_index": 0,
        "pembahasan": "penjelasan",
        "image_prompt": "deskripsi gambar dalam bahasa inggris (singkat & jelas)"
      }}
    ]
    """

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } if "gpt-4" in TEXT_MODEL else None
        )
        
        raw_json = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data_soal = json.loads(raw_json)
        
        # Jika AI membungkus dalam key tertentu
        if isinstance(data_soal, dict):
            for k in data_soal:
                if isinstance(data_soal[k], list):
                    data_soal = data_soal[k]
                    break

        # Download Gambar
        for i, item in enumerate(data_soal):
            item['image_bytes'] = None
            if i < len(list_request) and list_request[i]['use_image']:
                # Tampilkan status di Streamlit agar user tidak mengira macet
                with st.status(f"Mengunduh gambar untuk soal {i+1}...", expanded=False):
                    img_data = fetch_image(item.get('image_prompt', 'educational object'))
                    if img_data:
                        item['image_bytes'] = img_data.getvalue() # Simpan sebagai bytes murni
        
        return data_soal, None
    except Exception as e:
        return None, str(e)

# --- 7. UI STREAMLIT ---
if 'hasil_soal' not in st.session_state:
    st.session_state.hasil_soal = None

with st.sidebar:
    st.title("⚙️ Konfigurasi")
    api_key = st.secrets.get("OPENAI_API_KEY") or st.text_input("API Key", type="password")
    
    if not api_key:
        st.warning("Masukkan API Key!")
        st.stop()

    kelas_sel = st.selectbox("Pilih Kelas", list(DATABASE_MATERI.keys()))
    mapel_sel = st.selectbox("Pilih Mapel", list(DATABASE_MATERI[kelas_sel].keys()))
    jml = st.slider("Jumlah Soal", 1, 5, 2)
    
    list_req = []
    for i in range(jml):
        with st.expander(f"Soal {i+1}"):
            t = st.selectbox("Materi", DATABASE_MATERI[kelas_sel][mapel_sel], key=f"t{i}")
            l = st.selectbox("Level", ["Mudah", "Sedang", "Sulit"], index=1, key=f"l{i}")
            img = st.checkbox("Gunakan Gambar", value=True, key=f"i{i}")
            list_req.append({"topik": t, "level": l, "use_image": img})
    
    generate_btn = st.button("🚀 Generate Soal", type="primary")

st.title("📚 Generator Soal SD Digital")

if generate_btn:
    with st.spinner("Sedang membuat soal..."):
        res, err = generate_all_data(api_key, kelas_sel, mapel_sel, list_req)
        if res:
            st.session_state.hasil_soal = res
        else:
            st.error(err)

if st.session_state.hasil_soal:
    # Button Download
    doc_download = create_docx(st.session_state.hasil_soal, mapel_sel, kelas_sel)
    st.download_button(
        "📥 Download Word (.docx)",
        data=doc_download,
        file_name=f"Soal_{mapel_sel}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    st.divider()
    
    # Pratinjau
    for item in st.session_state.hasil_soal:
        with st.container(border=True):
            st.subheader(f"Soal Nomor {item['no']}")
            st.write(item['soal'])
            
            # Tampilkan Gambar
            if item.get('image_bytes'):
                st.image(item['image_bytes'], width=400)
            elif "image_prompt" in item:
                # Jika bytes kosong tapi ada prompt, coba beri link cadangan
                st.caption(f"Ilustrasi: {item['image_prompt']}")
            
            # Opsi
            cols = st.columns(2)
            for i, opt in enumerate(item['opsi']):
                cols[i%2].info(opt)
            
            with st.expander("Lihat Kunci & Pembahasan"):
                st.success(f"Kunci: {item['opsi'][item['kunci_index']]}")
                st.write(item['pembahasan'])
