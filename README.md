# 🔗 LinkMEdin — AI-Powered LinkedIn Post Automation

LinkMEdin is a local utility tool that transforms your raw ideas into professional LinkedIn posts using AI, and automatically pastes them into the LinkedIn post composer via Playwright browser automation.

This project was developed with the assistance of an AI pair-programming companion using modern AI-assisted development techniques.

---

## ⚙️ How It Works

1. **AI Translation:** Your raw ideas are transformed into a professional, emoji-rich, hashtag-ready LinkedIn post via the Groq API (Llama 3.3).
2. **Secure Local Session:** Your LinkedIn session cookies are stored entirely on your local machine (`~/.linkedin_app_profile`), so you don't need to log in every time.
3. **Subprocess Architecture:** To prevent conflicts between Streamlit and Playwright, browser operations run as an independent background Python process (`linkedin_helper.py`).

---

## 🔧 Setup & Installation

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright Browser:**
   ```bash
   playwright install chromium
   ```

3. **API Key:**
   Get a free Groq API key from [console.groq.com/keys](https://console.groq.com/keys), then create a `.env` file and add it:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

4. **Launch the App:**
   * **Windows (Easy Way):** Double-click the `LinkMEdin.bat` file in the folder to start instantly.
   * **Manual Start:** Run the following command in your terminal:
     ```bash
     streamlit run app.py
     ```

---

## 📖 Step-by-Step Usage Guide

1. **Enter Your API Key:** Paste your Groq API key in the settings section on the left panel (available for free at console.groq.com). The key will be automatically saved to the `.env` file.
2. **Connect Your LinkedIn Account:** Click the **"🔐 Login to LinkedIn"** button in the left panel. Log in to your LinkedIn account from the browser window that opens, then close the browser. *(Your session is saved locally and won't ask for your password again).*
3. **Prepare Your Post:** Switch to the **"✍️ Create Post"** tab, write your raw idea, select a tone and language, then click **"Translate to LinkedIn Style"**.
4. **Auto-Paste:** Switch to the **"🤖 Auto Send"** tab and click **"🚀 Send & Paste to LinkedIn"**. The browser will navigate to your LinkedIn feed, open the post composer, and automatically paste your text.
5. **Share:** After reviewing the pasted content, manually click the "Post/Share" button to publish. *(For security reasons, the app does not post directly on your behalf — the final action is left to you).*

---

## 🛡️ Security & Privacy

Your API key and LinkedIn session cookies are never exported or sent anywhere — they are stored exclusively on your local machine. The `.gitignore` configuration ensures that these sensitive files are never accidentally pushed to GitHub.

---

**Developer:** Muhsin Kılıç (Computer Engineering Student, Selçuk University)
