# OpenAI Labs - Gemini Versions 🤖

Bu dosyalar, OpenAI Agents SDK kullanan lab notebook'larının Gemini API ile çalışacak şekilde yeniden yazılmış versiyonlarıdır.

## 📁 Dosyalar

### 1. `sales_automation_gemini.py`
**Lab 2 Gemini Versiyonu**
- ✅ Çoklu sales agent'ları 
- ✅ Paralel email üretimi
- ✅ En iyi email seçimi
- ✅ HTML dönüşüm
- ✅ SendGrid email gönderimi

**Çalıştırma:**
```bash
cd "/Users/dr.sam/Desktop/Agentic AI/2_openai"
python sales_automation_gemini.py
```

### 2. `research_automation_gemini.py`  
**Lab 4 Gemini Versiyonu**
- ✅ Araştırma planlama
- ✅ Web arama (DuckDuckGo - ÜCRETSİZ)
- ✅ Otomatik rapor yazımı
- ✅ Email ile rapor gönderimi
- ✅ Structured outputs

**Çalıştırma:**
```bash
cd "/Users/dr.sam/Desktop/Agentic AI/2_openai"  
python research_automation_gemini.py
```

### 3. `multi_model_agents_gemini.py`
**Lab 3 Gemini Versiyonu**
- ✅ Farklı "model" kişilikleri (DeepSeek, Gemini, Llama stilinde)
- ✅ Input/Output guardrails
- ✅ İsim tespiti koruması
- ✅ Structured outputs (Pydantic)

**Çalıştırma:**
```bash
cd "/Users/dr.sam/Desktop/Agentic AI/2_openai"
python multi_model_agents_gemini.py
```

## 🛠️ Kurulum

### 1. Environment Variables
`.env` dosyanızda şunları olduğundan emin olun:

```bash
GOOGLE_API_KEY=AIzaSyCXOeMjrcOa7yjIqehsNlqznoSc8g9lRFM
SENDGRID_API_KEY=your_sendgrid_api_key
PUSHOVER_USER=your_pushover_user
PUSHOVER_TOKEN=your_pushover_token
```

### 2. Email Adresleri
Her dosyada şu satırları kendi email adreslerinizle değiştirin:

```python
from_email="YOUR_VERIFIED_EMAIL@example.com"  # SendGrid'de doğrulanmış email
to_email="YOUR_EMAIL@example.com"             # Kendi email'iniz
```

### 3. Gerekli Paketler
Tüm gerekli paketler zaten `requirements.txt`'te mevcut:
- ✅ openai (Gemini için)
- ✅ sendgrid 
- ✅ beautifulsoup4 (Web scraping için)
- ✅ pydantic (Structured outputs için)

## 🚀 Özellikler

### ✅ OpenAI Agents SDK'ya İhtiyaç Yok
- Tüm agent fonksiyonları manuel olarak implemente edildi
- Gemini API ile tam uyumluluk
- OpenAI'a hiç bağımlılık yok

### ✅ Ücretsiz Web Search  
- OpenAI WebSearchTool yerine DuckDuckGo API kullanılıyor
- Tamamen ücretsiz (OpenAI'da $0.025/search)

### ✅ Structured Outputs
- Pydantic modelleri ile yapılandırılmış çıktılar
- JSON parsing ve validation

### ✅ Guardrails
- Input guardrails (isim tespiti)
- Output validation
- Güvenlik kontrolleri

## 🧪 Test Etme

### Sales Automation Test:
```bash
python sales_automation_gemini.py
```
➡️ 3 farklı sales agent'ı paralel çalıştırır ve en iyi email'i seçer

### Research Automation Test:
```bash
python research_automation_gemini.py
```
➡️ "Latest AI Agent frameworks in 2025" konusunda araştırma yapar

### Multi-Model Agents Test:  
```bash
python multi_model_agents_gemini.py
```
➡️ Guardrails test eder ve çoklu model kişiliklerini dener

## 🔧 Kustomizasyon

### 1. Agent Instructions Değiştirme
Her agent'ın `instructions` field'ını düzenleyebilirsiniz:

```python
agent = GeminiAgent(
    name="Custom Agent",
    instructions="Your custom instructions here..."
)
```

### 2. Email Templates 
Email formatlarını ve subject line'ları özelleştirebilirsiniz.

### 3. Search Queries
Research agent'ta arama terimlerini değiştirebilirsiniz.

## 🆚 Orijinal vs Gemini Versiyonu

| Özellik | OpenAI Agents SDK | Gemini Version |
|---------|------------------|----------------|
| **API Cost** | Yüksek | Düşük |
| **Web Search** | $0.025/search | Ücretsiz |
| **Model Variety** | Çoklu model | Gemini (çoklu kişilik) |
| **Setup** | SDK gerekli | Sadece OpenAI client |
| **Flexibility** | Kısıtlı | Tam kontrol |

## 🎯 Sonuç

Artık tüm OpenAI Labs'ı Gemini API ile çalıştırabilirsiniz:
- ✅ **Daha ucuz** (Gemini API rates)
- ✅ **Daha hızlı** (az dependency) 
- ✅ **Daha esnek** (tam kontrol)
- ✅ **Ücretsiz web search**

🚀 **Başlamaya hazırsınız!**
