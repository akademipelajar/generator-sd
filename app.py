import streamlit as st
import json
import requests

# --- KONFIGURASI ---
st.set_page_config(page_title="SoalGen SD", page_icon="🎓")

# --- FUNGSI AI ---
def generate_soal(api_key, model_name, data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Buatkan 1 soal pilihan ganda (PG) untuk siswa SD.
    - Kelas: {data['kelas']}
    - Mapel: {data['mapel']}
    - Topik: {data['topik']}
    - Level: {data['kesulitan']}
    
    Output WAJIB JSON Murni (tanpa markdown ```json):
    {{
        "soal_teks": "...",
        "opsi": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "kunci_jawaban": "index 0-3",
        "pembahasan": "..."
    }}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return None, f"Gagal ({response.status_code}): {response.text}"
        
        hasil = response.json()
        try:
            teks = hasil['candidates'][0]['content']['parts'][0]['text']
            teks_bersih = teks.replace("```json", "").replace("```", "").strip()
            return json.loads(teks_bersih), None
        except:
            return None, "Gagal memproses jawaban AI."
    except Exception as e:
        return None, str(e)

# --- TAMPILAN APLIKASI ---
st.title("🎓 Generator Soal SD")
st.caption("Powered by Google Gemini")

# --- LOGIKA KUNCI RAHASIA (AUTO KEY) ---
# Cek apakah kunci ada di 'Secrets' Streamlit Cloud?
if "GOOGLE_API_KEY" in st.secrets:
    # Jika ada, pakai langsung!
    api_key = st.secrets["GOOGLE_API_KEY"]
    hide_api_input = True
else:
    # Jika tidak ada (misal lagi di localhost), minta input manual
    api_key = ""
    hide_api_input = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    # Hanya tampilkan kotak input jika kunci belum ditanam
    if not hide_api_input:
        api_key = st.text_input("API Key Gemini", type="password")
        st.info("Masukkan Key manual, atau set di Secrets saat deploy.")
    else:
        st.success("✅ API Key Terhubung Otomatis")
    
    # Menu Pilihan Model (Jaga-jaga kalau error)
    model_pilihan = st.selectbox("Versi AI", [
        "gemini-1.5-flash", 
        "gemini-2.5-flash",
        "gemini-pro"
    ])
    
    st.divider()
    kelas = st.selectbox("Kelas", ["1 SD", "2 SD", "3 SD", "4 SD", "5 SD", "6 SD"])
    mapel = st.selectbox("Mata Pelajaran", ["Matematika", "IPA", "Bahasa Indonesia", "Bahasa Inggris"])
    topik = st.text_input("Bab / Topik", "Pecahan")
    st.write("Tingkat Kesulitan:")
    kesulitan = st.radio("Level", ["Mudah", "Sedang", "Sulit"], label_visibility="collapsed")

# --- TOMBOL UTAMA ---
if st.button("🚀 Buat Soal", type="primary"):
    if not api_key:
        st.error("⚠️ API Key belum terisi.")
    elif not topik:
        st.warning("⚠️ Masukkan Topik dulu.")
    else:
        with st.spinner(f'Sedang berpikir ({model_pilihan})...'):
            soal, error = generate_soal(api_key, model_pilihan, {
                "kelas": kelas, "mapel": mapel, 
                "topik": topik, "kesulitan": kesulitan
            })
            
        if error:
            st.error("Terjadi Error:")
            st.code(error)
        elif soal:
            st.success("Berhasil!")
            with st.container(border=True):
                st.subheader("Pertanyaan:")
                st.write(f"**{soal['soal_teks']}**")
                jawaban_user = st.radio("Pilih jawaban:", soal['opsi'])
                st.divider()
                if st.button("🔍 Cek Jawaban"):
                    kunci_idx = int(soal['kunci_jawaban'])
                    kunci_teks = soal['opsi'][kunci_idx]
                    if jawaban_user == kunci_teks:
                        st.success("✅ BENAR!")
                        st.balloons()
                    else:
                        st.error(f"❌ SALAH. Jawaban: {kunci_teks}")
                    st.info(f"**Pembahasan:** {soal['pembahasan']}")