"""
LinkMEdin - LinkedIn Post Automation Tool
=========================================
A Streamlit web interface to draft posts using Groq LLM models
and automate posting inside LinkedIn's editor using Playwright.
"""

# Imports
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st

# Ortam değişkenleri — app.py ile aynı klasördeki .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

# Groq API (ücretsiz)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Playwright — sadece kurulu olup olmadığını kontrol etmek için
try:
    import playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Playwright'in kurulu olduğu Python yorumlayıcısını bul
# Windows Store Python 3.12 — playwright buraya kuruldu
_PY_WIN_STORE = r"C:\Users\Muhsin\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe"
import shutil as _shutil
if _shutil.which(_PY_WIN_STORE.replace('\\', '/')) or Path(_PY_WIN_STORE).exists():
    PYTHON_EXE = _PY_WIN_STORE
else:
    # Fallback: py launcher veya mevcut executable
    PYTHON_EXE = "py" if _shutil.which("py") else sys.executable


# Constants

PROFILE_DIR    = str(Path.home() / ".linkedin_app_profile")
LINKEDIN_URL   = "https://www.linkedin.com/feed/"
LOGIN_URL      = "https://www.linkedin.com/login"
DEFAULT_MODEL  = "llama-3.3-70b-versatile"
ENV_FILE       = Path(__file__).parent / ".env"
HELPER_SCRIPT  = str(Path(__file__).parent / "linkedin_helper.py")

SYSTEM_PROMPT = """Sen profesyonel bir LinkedIn içerik uzmanısın. Kullanıcının verdiği ham fikri veya metni,
aşağıdaki kurallara uygun şekilde profesyonel bir LinkedIn gönderisine dönüştür:

KURALLAR:
1. İlk cümle dikkat çekici ve kısa olmalı (hook).
2. Paragraflar kısa ve kolay okunabilir olmalı (2-3 cümle).
3. Paragraflar arasında boş satır bırak.
4. Uygun yerlerde emojiler kullan (abartma, doğal olsun).
5. Son paragrafta okuyucuya bir soru sor veya harekete geçirici mesaj ver (CTA).
6. En sona 3-5 adet ilgili hashtag ekle.
7. Profesyonel ama samimi bir ton kullan.
8. Metnin dili, kullanıcının yazdığı dille aynı olsun.
9. Metni LinkedIn'e uygun formatta, düz metin olarak üret (markdown kullanma).
10. Toplam uzunluk 1300 karakteri geçmesin.

Sadece dönüştürülmüş gönderi metnini döndür, başka açıklama ekleme."""


# ═══════════════════════════════════════════════════════════════
# SAYFA YAPILANDIRMASI VE CSS
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="LinkMEdin — LinkedIn Gönderi Otomasyonu",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Apply font only to text content and input controls, avoiding icon fonts */
    html, body, [data-testid="stAppViewContainer"], .stApp, p, span, h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
    }
    .stTextArea textarea, .stTextInput input, .stButton button, .stSelectbox select {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(145deg, #0a0a0f 0%, #0d1117 40%, #111827 100%);
    }

    .hero-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0a66c2 50%, #004182 100%);
        border-radius: 20px;
        padding: 2.2rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(10, 102, 194, 0.25);
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 60%);
        animation: shimmer 6s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        50% { transform: translate(10%, 10%) rotate(5deg); }
    }
    .hero-card h1 {
        color: #ffffff; font-size: 2rem; font-weight: 700;
        margin: 0 0 0.3rem 0; position: relative; z-index: 1;
        text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .hero-card p {
        color: rgba(255,255,255,0.8); font-size: 1rem;
        margin: 0; position: relative; z-index: 1;
    }

    .status-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
    }
    .status-card:hover {
        border-color: rgba(10,102,194,0.3);
        box-shadow: 0 4px 20px rgba(10,102,194,0.1);
    }
    .status-online  { border-left: 4px solid #10b981; }
    .status-offline { border-left: 4px solid #ef4444; }
    .status-warning { border-left: 4px solid #f59e0b; }

    .stButton > button {
        background: linear-gradient(135deg, #0a66c2 0%, #004182 100%);
        color: white !important;
        border: none; border-radius: 12px;
        padding: 0.65rem 1.5rem;
        font-weight: 600; font-size: 0.95rem;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        box-shadow: 0 4px 14px rgba(10,102,194,0.3);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(10,102,194,0.45);
        background: linear-gradient(135deg, #0b7dda 0%, #005bb5 100%);
    }

    .stTextArea textarea {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #e5e7eb !important;
        font-size: 0.95rem !important;
        padding: 1rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #0a66c2 !important;
        box-shadow: 0 0 0 2px rgba(10,102,194,0.2) !important;
    }

    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #e5e7eb !important;
        padding: 0.6rem 1rem !important;
    }
    .stTextInput input:focus {
        border-color: #0a66c2 !important;
        box-shadow: 0 0 0 2px rgba(10,102,194,0.2) !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #111827 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .section-divider {
        border: none; height: 1px;
        background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent);
        margin: 2rem 0;
    }

    .footer {
        text-align: center;
        color: rgba(255,255,255,0.25);
        font-size: 0.75rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 3rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.03);
        border-radius: 10px 10px 0 0;
        border: 1px solid rgba(255,255,255,0.06);
        border-bottom: none;
        padding: 0.5rem 1.2rem;
        color: #9ca3af;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(10,102,194,0.15) !important;
        color: #60a5fa !important;
        border-color: rgba(10,102,194,0.3) !important;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════

def save_groq_api_key(api_key: str) -> None:
    """Groq API anahtarını kalıcı olarak .env dosyasına kaydeder."""
    lines = []
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    key_found = False
    new_lines = []
    for line in lines:
        if line.startswith("GROQ_API_KEY="):
            new_lines.append(f"GROQ_API_KEY={api_key}\n")
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        new_lines.append(f"GROQ_API_KEY={api_key}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ["GROQ_API_KEY"] = api_key


def get_groq_api_key() -> str | None:
    """Groq API anahtarını session state > env değişkeni sırasıyla arar."""
    if "groq_api_key" in st.session_state and st.session_state.groq_api_key:
        return st.session_state.groq_api_key
    return os.environ.get("GROQ_API_KEY", "") or None


def check_linkedin_session() -> bool:
    """Kalıcı profil klasörünün varlığını kontrol eder."""
    p = Path(PROFILE_DIR)
    return p.exists() and any(p.iterdir())


def transform_to_linkedin_post(raw_text: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """Ham metni Groq API ile profesyonel LinkedIn gönderisine dönüştürür."""
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Aşağıdaki ham fikri profesyonel bir LinkedIn gönderisine dönüştür:\n\n{raw_text}"},
        ],
        temperature=0.7,
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()


def open_linkedin_login() -> None:
    """
    linkedin_helper.py'yi playwright'in kurulu olduğu Python süreci olarak başlatır.
    Windows'ta yeni konsol penceresi açar. Streamlit thread'ini bloklamaz.
    """
    if getattr(sys, 'frozen', False):
        cmd = [sys.executable, "helper", "login"]
    else:
        cmd = [PYTHON_EXE, HELPER_SCRIPT, "login"]
        if PYTHON_EXE == "py":
            cmd = ["py", "-3.12", HELPER_SCRIPT, "login"]
            
    subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )


def paste_to_linkedin(post_text: str) -> None:
    """
    Gönderi metnini geçici dosyaya yazar ve linkedin_helper.py'yi
    paste_file moduyla ayrı süreçte çalıştırır.
    """
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False,
        encoding="utf-8", dir=Path(__file__).parent,
    )
    tmp.write(post_text)
    tmp.close()

    if getattr(sys, 'frozen', False):
        cmd = [sys.executable, "helper", "paste_file", tmp.name]
    else:
        cmd = [PYTHON_EXE, HELPER_SCRIPT, "paste_file", tmp.name]
        if PYTHON_EXE == "py":
            cmd = ["py", "-3.12", HELPER_SCRIPT, "paste_file", tmp.name]
            
    subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )


# Session State Initialization

if "generated_post"      not in st.session_state: st.session_state.generated_post = ""
if "edited_post_area"    not in st.session_state: st.session_state.edited_post_area = ""
if "generation_history"  not in st.session_state: st.session_state.generation_history = []


# Sidebar Layout

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0 1.5rem 0;">
        <div style="font-size:2.5rem; margin-bottom:0.3rem;">🔗</div>
        <div style="font-size:1.2rem; font-weight:700; color:#60a5fa;">LinkMEdin</div>
        <div style="font-size:0.75rem; color:#6b7280; margin-top:0.2rem;">Gönderi Otomasyonu</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Sistem Durumu")

    # Playwright durumu
    if PLAYWRIGHT_AVAILABLE:
        st.markdown('<div class="status-card status-online">✅ Playwright hazır</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-card status-offline">❌ Playwright kurulu değil<br><code>pip install playwright && playwright install chromium</code></div>', unsafe_allow_html=True)

    # Groq durumu
    if GROQ_AVAILABLE:
        st.markdown('<div class="status-card status-online">✅ Groq SDK hazır (ücretsiz)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-card status-offline">❌ Groq kurulu değil<br><code>pip install groq</code></div>', unsafe_allow_html=True)

    # LinkedIn oturum durumu
    if check_linkedin_session():
        st.markdown('<div class="status-card status-online">🔐 LinkedIn profili mevcut</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-card status-warning">⚠️ LinkedIn girişi gerekli</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔑 API Ayarları")

    # Ücretsiz anahtar linki
    st.markdown("""
    <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2);
                border-radius:10px; padding:0.8rem; margin-bottom:0.8rem; font-size:0.82rem; color:#9ca3af;">
        🆓 <strong style="color:#10b981;">Groq ücretsizdir!</strong><br>
        Anahtar: <a href="https://console.groq.com/keys" target="_blank" style="color:#60a5fa;">console.groq.com/keys</a>
    </div>
    """, unsafe_allow_html=True)

    # Mevcut .env anahtarını maskeli göster
    current_saved_key = os.environ.get("GROQ_API_KEY", "")
    if current_saved_key:
        masked = current_saved_key[:8] + "..." + current_saved_key[-4:]
        st.markdown(f'<div class="status-card status-online">🌐 .env anahtarı: <code>{masked}</code></div>', unsafe_allow_html=True)

    # API anahtarı input — mevcut değeri doldurulmuş göster
    api_key_input = st.text_input(
        "Groq API Anahtarı",
        type="password",
        value=current_saved_key,
        placeholder="gsk_...",
        help="console.groq.com/keys adresinden ücretsiz alın.",
        key="sidebar_api_key",
    )
    if api_key_input and api_key_input != current_saved_key:
        st.session_state.groq_api_key = api_key_input
        save_groq_api_key(api_key_input)
        st.success("✅ API anahtarı .env dosyasına kaydedildi")
    elif api_key_input:
        st.session_state.groq_api_key = api_key_input

    # Model seçimi
    model_choice = st.selectbox(
        "AI Modeli",
        options=["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
        index=0,
        help="Hepsi ücretsizdir.",
    )

    st.markdown("---")
    st.markdown("### ⚡ Hızlı Eylemler")

    if st.button("🔐 LinkedIn Girişi Yap", key="sidebar_login", use_container_width=True):
        if not PLAYWRIGHT_AVAILABLE:
            st.error("Playwright kurulu değil!")
        else:
            open_linkedin_login()
            st.info("🌐 Tarayıcı açıldı! LinkedIn'e giriş yapın, ardından tarayıcıyı kapatın.")

    if st.button("🗑️ Profili Sıfırla", key="reset_profile", use_container_width=True):
        import shutil
        profile_path = Path(PROFILE_DIR)
        if profile_path.exists():
            shutil.rmtree(PROFILE_DIR, ignore_errors=True)
            st.success("Profil silindi.")
            st.rerun()
        else:
            st.info("Profil zaten mevcut değil.")

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#4b5563; font-size:0.7rem; padding-top:1rem;">
        LinkMEdin v1.0<br>Created by Muhsin Kılıç
    </div>
    """, unsafe_allow_html=True)


# Main Content Layout
# -------------------

st.markdown("""
<div class="hero-card">
    <h1>🚀 LinkMEdin</h1>
    <p>Ham fikirlerinizi profesyonel LinkedIn gönderilerine dönüştürün</p>
</div>
""", unsafe_allow_html=True)

tab_compose, tab_automate, tab_history = st.tabs(["✍️ Gönderi Oluştur", "🤖 Otomatik Gönder", "📜 Geçmiş"])


# Tab 1: Compose Post

with tab_compose:
    st.markdown("#### 💡 Ham Fikrinizi Yazın")
    st.caption("Aklınızdaki fikri aşağıya yazın. AI onu LinkedIn'e uygun profesyonel bir gönderiye dönüştürecek.")

    raw_input = st.text_area(
        "Ham Metin",
        placeholder="Örnek: Bugün bir müşteri toplantısında sunum yaptım, gerçekten güzel geri dönüşler aldım...",
        height=180,
        key="raw_text_input",
        label_visibility="collapsed",
    )

    if raw_input:
        char_count = len(raw_input)
        color = "#f59e0b" if char_count > 2000 else "#6b7280"
        st.markdown(f'<div style="text-align:right; color:{color}; font-size:0.8rem;">{char_count} karakter</div>', unsafe_allow_html=True)

    col_tone, col_lang = st.columns(2)
    with col_tone:
        tone = st.selectbox("🎨 Ton", ["Profesyonel & Samimi", "İlham Verici", "Eğitici", "Hikaye Anlatıcı", "Kısa & Net"], index=0)
    with col_lang:
        lang = st.selectbox("🌐 Dil", ["Türkçe", "İngilizce", "Otomatik (girdi diline göre)"], index=0)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if st.button("✨ Metni LinkedIn Diline Çevir", key="transform_btn", use_container_width=True):
        if not raw_input or not raw_input.strip():
            st.warning("⚠️ Lütfen önce bir metin yazın.")
        elif not GROQ_AVAILABLE:
            st.error("❌ Groq kurulu değil. `pip install groq` komutunu çalıştırın.")
        else:
            api_key = get_groq_api_key()
            if not api_key:
                st.error("❌ Groq API anahtarı bulunamadı. Sol panelden anahtarınızı girin (console.groq.com/keys — ücretsiz).")
            else:
                with st.spinner("🧠 AI gönderiyi hazırlıyor..."):
                    try:
                        enriched = f"[Ton: {tone}] [Dil: {lang}]\n\n{raw_input}"
                        generated = transform_to_linkedin_post(enriched, api_key, model_choice)
                        st.session_state.generated_post = generated
                        st.session_state.edited_post_area = generated  # Force-update text_area widget state
                        st.session_state.generation_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "raw": raw_input[:100] + "..." if len(raw_input) > 100 else raw_input,
                            "generated": generated,
                        })
                        st.success("✅ Gönderi başarıyla oluşturuldu!")
                    except Exception as e:
                        st.error(f"❌ AI hatası: {str(e)}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("#### 📝 Oluşturulan LinkedIn Gönderisi")
    st.caption("Gönderiyi düzenleyebilir, ardından 'Otomatik Gönder' sekmesinden LinkedIn'e yapıştırabilirsiniz.")

    edited_post = st.text_area(
        "LinkedIn Gönderisi",
        value=st.session_state.generated_post,
        height=280,
        key="edited_post_area",
        label_visibility="collapsed",
        placeholder="AI tarafından oluşturulan gönderi burada görünecek...",
    )
    if edited_post != st.session_state.generated_post:
        st.session_state.generated_post = edited_post

    if edited_post:
        post_len   = len(edited_post)
        word_count = len(edited_post.split())
        hash_count = edited_post.count("#")
        col1, col2, col3 = st.columns(3)
        color = "#10b981" if post_len <= 1300 else ("#f59e0b" if post_len <= 3000 else "#ef4444")
        for col, val, label in [(col1, post_len, "karakter"), (col2, word_count, "kelime"), (col3, hash_count, "hashtag")]:
            with col:
                st.markdown(f"""
                <div style="text-align:center; padding:0.5rem; background:rgba(255,255,255,0.03);
                            border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
                    <div style="font-size:1.5rem; font-weight:700; color:{color if label=='karakter' else '#60a5fa'};">{val}</div>
                    <div style="font-size:0.75rem; color:#9ca3af;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑️ Temizle", key="clear_post"):
            st.session_state.generated_post = ""
            st.session_state.edited_post_area = ""
            st.rerun()


# Tab 2: Automate Posting

with tab_automate:
    st.markdown("#### 🤖 LinkedIn'e Otomatik Yapıştır")
    st.caption("Hazırladığınız gönderiyi LinkedIn paylaşım editörüne otomatik olarak yapıştırır. Gönderiyi kendiniz yayınlarsınız.")

    if not PLAYWRIGHT_AVAILABLE:
        st.error("""
        ❌ **Playwright kurulu değil!**
        ```
        pip install playwright
        playwright install chromium
        ```
        """)
    else:
        # Oturum durumu
        if not check_linkedin_session():
            st.markdown("""
            <div class="status-card status-warning">
                <strong>⚠️ LinkedIn Oturumu Gerekli</strong><br>
                <span style="color:#9ca3af;">Otomatik yapıştırma için önce LinkedIn'e giriş yapmalısınız.</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔐 LinkedIn Girişi Yap", key="main_login", use_container_width=True):
                open_linkedin_login()
                st.info("🌐 Tarayıcı açıldı! LinkedIn'e giriş yapın, ardından tarayıcıyı kapatın.")
        else:
            st.markdown("""
            <div class="status-card status-online">
                <strong>✅ LinkedIn Oturumu Aktif</strong><br>
                <span style="color:#9ca3af;">Kalıcı profil ile otomatik giriş hazır.</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("##### 📋 Gönderilecek Metin Önizlemesi")

        current_post = st.session_state.generated_post
        if current_post:
            st.markdown(f"""
            <div class="status-card" style="white-space:pre-wrap; color:#d1d5db; font-size:0.9rem; line-height:1.6;">
{current_post}
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

            st.info("""
            **📌 Nasıl çalışır?**
            1. Ayrı bir tarayıcı penceresi açılır ve LinkedIn feed sayfasına gider.
            2. 'Gönderi başlat' butonuna otomatik tıklanır.
            3. Metniniz editöre yapıştırılır.
            4. ⚠️ **Gönderi paylaşılmaz!** Tarayıcı açık kalır, siz kontrol edip paylaşırsınız.
            """)

            if st.button("🚀 LinkedIn'e Gönder ve Yapıştır", key="paste_btn", use_container_width=True):
                paste_to_linkedin(current_post)
                st.success("🤖 Tarayıcı açılıyor! Birkaç saniye içinde LinkedIn'e gidecek ve metni yapıştıracak.")
                st.balloons()
        else:
            st.markdown("""
            <div class="status-card status-warning">
                <strong>📝 Henüz gönderi hazırlanmadı</strong><br>
                <span style="color:#9ca3af;">Önce "Gönderi Oluştur" sekmesinden bir gönderi hazırlayın.</span>
            </div>
            """, unsafe_allow_html=True)


# Tab 3: Post History

with tab_history:
    st.markdown("#### 📜 Gönderi Geçmişi")
    st.caption("Bu oturumda oluşturduğunuz gönderilerin kaydı.")

    if st.session_state.generation_history:
        for i, entry in enumerate(reversed(st.session_state.generation_history)):
            with st.expander(f"📄 {entry['timestamp']} — {entry['raw'][:60]}...", expanded=(i == 0)):
                st.markdown("**Ham Girdi:**")
                st.text(entry["raw"])
                st.markdown("**Oluşturulan Gönderi:**")
                st.markdown(f"""
                <div class="status-card" style="white-space:pre-wrap; color:#d1d5db; font-size:0.9rem;">
{entry['generated']}
                </div>
                """, unsafe_allow_html=True)
                if st.button("♻️ Bu gönderiyi kullan", key=f"reuse_{i}"):
                    st.session_state.generated_post = entry["generated"]
                    st.session_state.edited_post_area = entry["generated"]
                    st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem; color:#6b7280;">
            <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
            <p>Henüz gönderi oluşturulmadı.</p>
        </div>
        """, unsafe_allow_html=True)


# Footer

st.markdown("""
<div class="footer">
    <p>LinkMEdin — LinkedIn Otomatik Gönderi Hazırlama ve Otomasyon Uygulaması</p>
    <p>🔒 Verileriniz tamamen yerel bilgisayarınızda kalır.</p>
</div>
""", unsafe_allow_html=True)
