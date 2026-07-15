"""
LinkedIn Automation Helper
==========================
Handles Playwright browser automation for logging in and pasting posts
to LinkedIn. Run as a subprocess from the main Streamlit application.
"""

import sys
import os
import json
import time
from pathlib import Path

# Playwright
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def wait_for_page_close(page, timeout_ms=600000):
    """Sayfa kapatılana kadar bekler."""
    start_time = time.time()
    while not page.is_closed():
        if (time.time() - start_time) * 1000 > timeout_ms:
            break
        try:
            page.wait_for_timeout(1000)
        except Exception:
            break

# ─── Sabitler ───────────────────────────────────────────────
PROFILE_DIR = str(Path.home() / ".linkedin_app_profile")
LINKEDIN_FEED_URL  = "https://www.linkedin.com/feed/"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--no-first-run",
    "--no-default-browser-check",
    "--start-maximized",
]


def kill_hung_chromium():
    """Önceki oturumlardan kalan ve profil klasörünü kilitleyen chrome süreçlerini sonlandırır."""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'chrome.exe':
                    cmdline = proc.info['cmdline'] or []
                    if any('.linkedin_app_profile' in arg for arg in cmdline):
                        print(f"Kilitli Chromium süreci sonlandırılıyor: PID {proc.info['pid']}", flush=True)
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        print(f"Süreç temizleme hatası: {e}", flush=True)

def launch_context(playwright):
    """Kalıcı Chromium bağlamını başlatır."""
    kill_hung_chromium()
    return playwright.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        headless=False,
        args=BROWSER_ARGS,
        viewport={"width": 1280, "height": 900},
        locale="tr-TR",
        timezone_id="Europe/Istanbul",
        ignore_default_args=["--enable-automation"],
        chromium_sandbox=False,
    )


def cmd_login():
    """LinkedIn giriş sayfasını açar ve kullanıcı tarayıcıyı kapatana kadar bekler."""
    print("Tarayıcı açılıyor...", flush=True)
    with sync_playwright() as p:
        context = launch_context(p)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(LINKEDIN_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        print("LinkedIn giriş sayfası açıldı. Lütfen giriş yapın.", flush=True)
        # Kullanıcı tarayıcıyı kapatana kadar bekle
        try:
            wait_for_page_close(page, 600000)  # 10 dakika
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass
    print("DONE", flush=True)


def cmd_paste(post_text: str):
    """LinkedIn feed'e gidip gönderi editörüne metni yapıştırır."""
    print("LinkedIn açılıyor...", flush=True)
    with sync_playwright() as p:
        context = launch_context(p)
        page = context.pages[0] if context.pages else context.new_page()

        # LinkedIn feed'e git
        page.goto(LINKEDIN_FEED_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        print("LinkedIn açıldı.", flush=True)

        # Giriş kontrolü
        if "login" in page.url or "checkpoint" in page.url:
            print("ERROR: LinkedIn oturumu bulunamadı.", flush=True)
            try:
                wait_for_page_close(page, 300000)
            except Exception:
                pass
            context.close()
            return

        # "Gönderi başlat" butonunu bul
        start_post_selectors = [
            "text=Gönderi oluşturun",
            "text=Gönderi oluştur",
            "text=Gönderi başlat",
            "text=Start a post",
            "button:has-text('Gönderi oluşturun')",
            "button:has-text('Gönderi başlat')",
            "button:has-text('Start a post')",
            ".share-box-feed-entry__trigger",
            "[data-control-name='share.dashboard_entry_point']",
            ".artdeco-card .share-box-feed-entry__top-bar button",
            "div.share-box-feed-entry__top-bar button",
            ".share-box-feed-entry__closed-share-box",
        ]

        clicked = False
        for selector in start_post_selectors:
            try:
                el = page.locator(selector).first
                el.click(timeout=2000)
                clicked = True
                print(f"Buton bulundu: {selector}", flush=True)
                break
            except Exception:
                continue

        if not clicked:
            # Fallback: metne göre eşleşen herhangi bir elemente tıkla
            for kw in ["Gönderi oluşturun", "Gönderi oluştur", "Gönderi başlat", "Start a post"]:
                try:
                    el = page.get_by_text(kw).first
                    el.click(timeout=2000)
                    clicked = True
                    print(f"Fallback metin tıklandı: {kw}", flush=True)
                    break
                except Exception:
                    continue

        if not clicked:
            print("ERROR: 'Gönderi başlat' butonu bulunamadı.", flush=True)
            try:
                wait_for_page_close(page, 300000)
            except Exception:
                pass
            context.close()
            return

        # Editörün açılmasını bekle
        page.wait_for_timeout(2000)

        # Editörü bul
        editor = None
        for selector in [".ql-editor", "[role='textbox']", "[contenteditable='true']", "div[data-placeholder]"]:
            try:
                el = page.locator(selector).first
                el.wait_for(state="visible", timeout=3000)
                editor = el
                break
            except Exception:
                continue

        if not editor:
            print("ERROR: Editör bulunamadı.", flush=True)
            try:
                wait_for_page_close(page, 300000)
            except Exception:
                pass
            context.close()
            return

        # Metni yapıştır
        editor.click()
        page.wait_for_timeout(300)

        # Önce clipboard'a yaz, sonra Ctrl+V
        try:
            page.evaluate(
                "(text) => navigator.clipboard.writeText(text)",
                post_text,
            )
            page.wait_for_timeout(300)
            editor.press("Control+v")
        except Exception:
            try:
                editor.fill(post_text)
            except Exception:
                page.keyboard.type(post_text, delay=5)

        page.wait_for_timeout(500)
        print("SUCCESS: Metin yapıştırıldı!", flush=True)

        # Kullanıcı tarayıcıyı kapatana kadar bekle
        try:
            wait_for_page_close(page, 600000)
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python linkedin_helper.py [login|paste] [metin]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "login":
        cmd_login()

    elif command == "paste":
        if len(sys.argv) < 3:
            print("Kullanım: python linkedin_helper.py paste 'metin'")
            sys.exit(1)
        text = sys.argv[2]
        cmd_paste(text)

    elif command == "paste_file":
        # Uzun metinler için dosyadan oku
        if len(sys.argv) < 3:
            print("Kullanım: python linkedin_helper.py paste_file dosya.txt")
            sys.exit(1)
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            text = f.read()
        cmd_paste(text)

    else:
        print(f"Bilinmeyen komut: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
