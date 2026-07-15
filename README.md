# 🔗 LinkMEdin — Yapay Zeka Destekli LinkedIn Gönderi Otomasyonu

LinkMEdin, ham fikirlerinizi yapay zeka gücüyle profesyonel LinkedIn gönderilerine dönüştüren ve Playwright tarayıcı otomasyonu ile otomatik olarak LinkedIn paylaşım kutusuna yapıştıran yerel bir yardımcı araçtır.

Bu proje, modern yapay zeka pair-programming teknikleri kullanılarak asistan eşliğinde geliştirilmiştir.

---

## ⚙️ Nasıl Çalışır?

1. **Yapay Zeka Çevirisi:** Ham fikirleriniz, Groq API (Llama 3.3) aracılığıyla profesyonel, emojili ve hashtag'li bir LinkedIn gönderisine dönüştürülür.
2. **Yerel Güvenli Oturum:** LinkedIn oturum çerezleriniz tamamen yerel bilgisayarınızda (`~/.linkedin_app_profile`) saklanır. Bu sayede her seferinde giriş yapmanız gerekmez.
3. **Subprocess Mimarisi:** Streamlit ve Playwright'ın çakışmasını önlemek amacıyla tarayıcı işlemleri arka planda bağımsız bir Python süreci (`linkedin_helper.py`) olarak koşturulur.

---

## 🔧 Kurulum ve Çalıştırma

1. **Gereksinimleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Playwright Tarayıcısını Kurun:**
   ```bash
   playwright install chromium
   ```

3. **API Anahtarı:**
   [console.groq.com/keys](https://console.groq.com/keys) adresinden ücretsiz bir Groq API anahtarı alın ve `.env` dosyası oluşturup içine ekleyin:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```

4. **Uygulamayı Başlatın:**
   * **Windows için (Kolay Yol):** Klasördeki `LinkMEdin.bat` dosyasına çift tıklayarak anında başlatabilirsiniz.
   * **Manuel Başlatma:** Terminalden şu komutu çalıştırabilirsiniz:
     ```bash
     streamlit run app.py
     ```

---

## 📖 Adım Adım Kullanım Kılavuzu

1. **API Anahtarını Girin:** Sol paneldeki ayarlar bölümünden Groq API anahtarınızı yapıştırın (console.groq.com adresinden ücretsiz alınabilir). Anahtar otomatik olarak `.env` dosyasına kaydedilecektir.
2. **LinkedIn Hesabınızı Bağlayın:** Sol paneldeki **"🔐 LinkedIn Girişi Yap"** butonuna tıklayın. Açılan tarayıcı penceresinden LinkedIn hesabınıza bir kez giriş yapın ve ardından tarayıcıyı kapatın. *(Oturumunuz yerel klasörünüze kaydedilir ve bir daha şifre sormaz).*
3. **Gönderinizi Hazırlayın:** **"✍️ Gönderi Oluştur"** sekmesine geçip ham fikrinizi yazın, ton ve dil seçimi yaparak **"Metni LinkedIn Diline Çevir"** butonuna basın.
4. **Otomatik Yapıştırın:** **"🤖 Otomatik Gönder"** sekmesine geçin ve **"🚀 LinkedIn'e Gönder ve Yapıştır"** butonuna tıklayın. Açılan tarayıcı LinkedIn feed sayfasına gidip gönderi oluşturma kutusunu açacak ve metninizi otomatik olarak yapıştıracaktır.
5. **Paylaşın:** Yapıştırılan metni kontrol ettikten sonra manuel olarak "Paylaş/Gönder" butonuna basarak yayınlayabilirsiniz. *(Güvenlik nedeniyle uygulama gönderiyi sizin adınıza direkt paylaşmaz, son kontrolü size bırakır).*

---

## 🛡️ Güvenlik ve Gizlilik

API anahtarınız ve LinkedIn şifre/çerez oturum bilgileriniz kesinlikle dışarı aktarılmaz, sadece yerel makinenizde barındırılır. `.gitignore` yapılandırması sayesinde bu özel verilerin yanlışlıkla GitHub'a yüklenmesi tamamen engellenmiştir.

---

**Geliştirici:** Muhsin Kılıç (Selçuk Üniversitesi Bilgisayar Mühendisliği Öğrencisi)
