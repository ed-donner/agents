# 🐳 IntellaPersona - Docker Quick Start

## ⚠️ Sorunlar Düzeltildi!

### ❌ Sorun 1: OPENAI_API_KEY Eksik
```
WARN[0000] The "OPENAI_API_KEY" variable is not set
```
**Çözüm:** `.env` dosyası oluşturuldu ✅

### ❌ Sorun 2: Gradio 4.16 Yüklendi (Eski)
```
TypeError: BlockContext.__init__() got an unexpected keyword argument 'delete_cache'
```
**Çözüm:** Dockerfile `requirements_docker.txt` kullanacak şekilde güncellendi ✅

---

## 🚀 Hemen Başla (3 Adım)

### ADIM 1: OpenAI API Key Ekle (1 dakika)

```bash
cd /Users/gonenc_aydin/Desktop/The_Complete_AI_Agent_Course/agents/1_foundations

# .env dosyasını düzenle
nano .env

# Ya da VSCode'da:
code .env
```

**Düzenle:**
```env
OPENAI_API_KEY=sk-proj-your-actual-key-here  # ← Buraya gerçek key'ini yapıştır
```

**OpenAI API Key Nereden?**
- https://platform.openai.com/api-keys
- "Create new secret key"
- Key'i kopyala ve .env'e yapıştır

**Kaydet ve kapat!**

---

### ADIM 2: Docker Rebuild (2 dakika)

```bash
# Eski container'ı durdur
docker-compose down

# Cache'i temizle ve yeniden build et
docker-compose build --no-cache

# Gradio 5.x yüklenecek! (>=5.0.0)
```

**Beklenen Output:**
```
[+] Building 120.5s (13/13) FINISHED
...
 => [5/7] RUN pip install --no-cache-dir -r requirements.txt
 => Installing gradio>=5.0.0                              ✅
 => Installing openai>=1.50.0                             ✅
...
 => exporting to image
Successfully built
```

---

### ADIM 3: Docker Run (1 dakika)

```bash
docker-compose up
```

**Beklenen Output:**
```
intellapersona  | ✅ Loaded intellecta_website.md into KB (company)
intellapersona  | ✅ Loaded intellecta_cli.md into KB (llmops)
...
intellapersona  | ✅ Loaded 27 files into KB
intellapersona  | ✅ Knowledge Base initialized (27 documents)
intellapersona  | Running on local URL:  http://0.0.0.0:7860
intellapersona  | 
intellapersona  | To create a public link, set `share=True` in `launch()`.
```

**✅ BAŞARILI!**

---

## 🌐 Test Et

### Browser'da Aç:
```
http://localhost:7860
```

### Test Checklist:
- [ ] ✅ Carousel görünüyor ve scroll oluyor
- [ ] ✅ Logo görünüyor (IntellectaLinkedIn.png avatar)
- [ ] ✅ "Get Started" butonu çalışıyor
- [ ] ✅ Login/Sign up açılıyor
- [ ] ✅ Visitor account oluşturuluyor
- [ ] ✅ Chat'te mesaj gönderilebiliyor
- [ ] ✅ Bot response geliyor (GPT-4)
- [ ] ✅ Autoscroll çalışıyor (yeni mesajlar)
- [ ] ✅ State.change() events çalışıyor (tab geçişleri)
- [ ] ✅ RAG çalışıyor (test: "Kubernetes deneyimin nedir?")

---

## 🎯 Tüm Özellikler Aktif mi?

### 1. delete_cache ✅
```bash
# Container logs'da göreceksin:
intellapersona  | Cache cleanup scheduled (weekly)
```

### 2. Chatbot type="messages" ✅
```bash
# Modern dict-based format
intellapersona  | Chatbot initialized with messages type
```

### 3. autoscroll ✅
```bash
# Yeni mesaj geldiğinde otomatik scroll
# Browser'da test et: Chat'e mesaj gönder, otomatik aşağı kayacak
```

### 4. avatar_images ✅
```bash
# Logo görünecek
intellapersona  | Avatar images loaded: IntellectaLinkedIn.png
```

### 5. State.change() Events (x5) ✅
```bash
# Login yap, tablar arasında geç
# İçerikler reactive olarak güncellenecek
```

---

## 🔧 Sorun Giderme

### Sorun: Hala "delete_cache" Hatası

**Neden:** Docker cache'de eski image var

**Çözüm:**
```bash
# Tüm cache'i temizle
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

---

### Sorun: OPENAI_API_KEY Hatası

**Semptom:**
```
Error generating embedding: Connection error
```

**Çözüm:**
```bash
# 1. .env dosyasını kontrol et
cat .env

# 2. API key doğru mu?
# sk-proj-... ile başlamalı

# 3. Restart
docker-compose restart
```

---

### Sorun: Port 7860 Kullanımda

**Semptom:**
```
Error: Bind for 0.0.0.0:7860 failed: port is already allocated
```

**Çözüm 1: Mevcut container'ı durdur**
```bash
docker-compose down
docker-compose up
```

**Çözüm 2: Farklı port kullan**
```bash
# docker-compose.yml'de değiştir:
ports:
  - "8080:7860"  # 8080 kullan

# Sonra:
docker-compose up
# Browser: http://localhost:8080
```

---

### Sorun: Knowledge Base Yüklenmiyor

**Semptom:**
```
intellapersona  | ❌ Failed to load knowledge files
```

**Çözüm:**
```bash
# me/ klasörü var mı kontrol et
ls -la me/

# Dockerfile'da me/ copy edilmiş mi?
cat Dockerfile | grep "COPY me/"

# Rebuild
docker-compose build --no-cache
docker-compose up
```

---

## 📊 Docker Commands (Reference)

### Build & Run
```bash
docker-compose build              # Build image
docker-compose build --no-cache   # Build without cache
docker-compose up                 # Run (foreground)
docker-compose up -d              # Run (background)
docker-compose down               # Stop and remove
docker-compose restart            # Restart
```

### Logs & Debug
```bash
docker-compose logs               # Show all logs
docker-compose logs -f            # Follow logs
docker-compose logs -f --tail 50  # Last 50 lines
docker logs intellapersona        # Container logs
```

### Container Management
```bash
docker-compose ps                 # Show running containers
docker-compose exec intellapersona bash  # Enter container
docker-compose stop               # Stop containers
docker-compose start              # Start stopped containers
```

### Cleanup
```bash
docker-compose down -v            # Remove volumes too
docker system prune -a            # Clean all unused
docker volume prune               # Clean volumes
```

---

## 🎉 Başarılı Deployment!

**Eğer şunları görüyorsan:**
```
✅ Loaded 27 files into KB
✅ Knowledge Base initialized
Running on http://0.0.0.0:7860
```

**VE:**
- Carousel scroll ediyor ✅
- Logo görünüyor ✅
- Chat çalışıyor ✅
- RAG response geliyor ✅

**TEBR İKLER! Docker deployment başarılı! 🎉**

---

## 🚀 Sırada Ne Var?

### Option 1: Production Deploy (Railway)
```bash
git add .
git commit -m "Docker deployment with full features"
git push

# Railway.app → New Project → Deploy from GitHub
# Environment variables: OPENAI_API_KEY
```

### Option 2: AWS Spot Deploy
```bash
# EC2 instance başlat
# SSH ile bağlan
# Git clone
# docker-compose up -d
```

### Option 3: Local'de Devam
```bash
# Background'da çalıştır
docker-compose up -d

# Logs izle
docker-compose logs -f
```

---

## 📝 .env Template

```env
# IntellaPersona Environment Variables
# ======================================

# REQUIRED: OpenAI API Key
OPENAI_API_KEY=sk-proj-your-actual-key-here

# OPTIONAL: PushOver Notifications
PUSHOVER_USER_KEY=
PUSHOVER_API_TOKEN=

# OPTIONAL: Custom Settings
# PORT=7860
# HOST=0.0.0.0
```

---

## ✅ Final Checklist

- [ ] ✅ .env dosyası oluşturuldu
- [ ] ✅ OPENAI_API_KEY eklendi
- [ ] ✅ Dockerfile güncellendi (requirements_docker.txt)
- [ ] ✅ docker-compose.yml güncellendi (version removed)
- [ ] ✅ docker-compose build --no-cache çalıştırıldı
- [ ] ✅ docker-compose up çalıştırıldı
- [ ] ✅ http://localhost:7860 açıldı
- [ ] ✅ Tüm özellikler test edildi
- [ ] ✅ Knowledge Base yüklendi (27 files)
- [ ] ✅ RAG çalışıyor

---

**ŞİMDİ:**

1. **nano .env** → API key ekle
2. **docker-compose build --no-cache** → Rebuild
3. **docker-compose up** → Run
4. **http://localhost:7860** → Test!

**HAYDİ BAŞLA! 🐳🚀**
