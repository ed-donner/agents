# TLS & mTLS Certificates — Complete Guide

---

## What is a Certificate?

A **digital certificate** is an electronic document that:
- Proves the identity of a server (or client)
- Contains a **public key**
- Is signed by a trusted **Certificate Authority (CA)**

Think of it like a **digital passport** — issued by a trusted authority, proving who you are.

---

## TLS — Transport Layer Security

### What is TLS?

TLS is a **cryptographic protocol** that provides:
- **Encryption** — data is unreadable to eavesdroppers
- **Authentication** — server proves its identity to the client
- **Integrity** — data is not tampered with in transit

> HTTPS = HTTP + TLS

---

### TLS Handshake (One-Way)

```
Client                          Server
  |                               |
  |--- ClientHello -------------> |  (supported cipher suites)
  |                               |
  |<-- ServerHello + Certificate -|  (server proves identity)
  |                               |
  |--- Key Exchange ------------> |
  |                               |
  |<======= Encrypted Data ======>|
```

**Only the server is authenticated.**
The client is anonymous.

---

### Where is TLS Used?

| Use Case              | Example                        |
|-----------------------|--------------------------------|
| Web browsers          | `https://yourbank.com`         |
| Email                 | SMTP/IMAP over TLS             |
| APIs                  | REST APIs with HTTPS           |
| Databases             | PostgreSQL SSL connections     |
| Cloud services        | AWS, Azure, GCP endpoints      |
| Mobile apps           | App ↔ Backend communication   |

---

### Benefits of TLS

| Benefit          | Explanation                                      |
|------------------|--------------------------------------------------|
| Privacy          | Encrypts all data in transit                     |
| Trust            | Users know they're on the real website           |
| SEO Boost        | Google ranks HTTPS sites higher                  |
| Compliance       | Required for PCI-DSS, HIPAA, GDPR                |
| Browser trust    | No "Not Secure" warning in browsers              |

---

## mTLS — Mutual TLS

### What is mTLS?

In standard TLS, **only the server** proves its identity.

In **mTLS**, **both** the client AND the server prove their identity.

> mTLS = Two-way authentication

---

### mTLS Handshake (Two-Way)

```
Client                              Server
  |                                   |
  |--- ClientHello -----------------> |
  |                                   |
  |<-- ServerHello + Certificate ---- |  (server proves identity)
  |                                   |
  |--- Client Certificate ----------> |  (client proves identity)
  |                                   |
  |--- Certificate Verify ----------> |  (client signs with private key)
  |                                   |
  |<======= Encrypted + Trusted =====>|
```

**Both sides are authenticated.**

---

### TLS vs mTLS — Quick Comparison

| Feature                  | TLS                    | mTLS                          |
|--------------------------|------------------------|-------------------------------|
| Server authenticated     | Yes                    | Yes                           |
| Client authenticated     | No                     | Yes                           |
| Certificate required     | Server only            | Both server and client        |
| Use case                 | Public websites        | Internal services, APIs, B2B  |
| Security level           | High                   | Very High                     |
| Setup complexity         | Low                    | Medium–High                   |

---

### Where is mTLS Used?

| Scenario                        | Why mTLS?                                     |
|---------------------------------|-----------------------------------------------|
| Microservices communication     | Service A must prove identity to Service B    |
| Zero Trust security             | Never trust, always verify both sides         |
| B2B API integrations            | Partner must present a valid cert to call API |
| Kubernetes service mesh         | Istio/Linkerd use mTLS between pods           |
| Banking & fintech               | Regulatory requirement for secure channels    |
| IoT devices                     | Device must prove identity before sending data|
| VPN alternatives                | Client cert replaces username/password        |

---

### Real-World mTLS Example

```
Payment Gateway (Client)          Your Bank API (Server)
        |                                  |
        |--- HTTPS + Client Cert --------> |
        |                                  |
        | Server checks: "Is this cert     |
        |  in my trusted CA list?"         |
        |                                  |
        |<-- 200 OK (Encrypted) ---------- |
```

Without the valid client certificate → **403 Forbidden**

---

## Certificate Types

| Type                    | Validates          | Use Case                             |
|-------------------------|--------------------|--------------------------------------|
| DV (Domain Validated)   | Domain only        | Blogs, personal sites                |
| OV (Organization Valid) | Domain + Org name  | Business websites                    |
| EV (Extended Valid)     | Full org identity  | Banks, e-commerce                    |
| Wildcard `*.domain.com` | All subdomains     | `api.example.com`, `app.example.com` |
| SAN (Multi-domain)      | Multiple domains   | `example.com` + `example.net`        |
| Client Certificate      | Client identity    | mTLS, user authentication            |

---

## Certificate Anatomy

```
Certificate:
├── Subject         → Who owns this cert (CN=example.com)
├── Issuer          → Who signed it (CA name)
├── Valid From      → Start date
├── Valid To        → Expiry date
├── Public Key      → Used for encryption
├── Signature       → CA's digital signature
└── SANs            → Extra domain names covered
```

---

## Certificate Authority (CA)

A **CA** is a trusted third party that:
- Verifies your identity
- Signs your certificate
- Is trusted by browsers/OS by default

### Types of CAs

| Type                | Examples                                      |
|---------------------|-----------------------------------------------|
| Public CA           | DigiCert, Sectigo, GlobalSign, Let's Encrypt  |
| Private/Internal CA | Your own CA for internal services             |
| Cloud CA            | AWS ACM, Azure Key Vault, GCP CAS             |

---

## Where to Buy / Get Certificates?

### Free (Automated)

| Provider          | Best For                       | Notes                         |
|-------------------|-------------------------------|-------------------------------|
| **Let's Encrypt** | Public websites, APIs         | 90-day auto-renew, free       |
| **ZeroSSL**       | Public websites               | Free tier available           |
| **AWS ACM**       | AWS-hosted services           | Free for AWS resources        |
| **Cloudflare**    | Sites behind Cloudflare       | Free, auto-managed            |

### Paid (For Business/EV)

| Provider         | Best For                        | Price Range         |
|------------------|---------------------------------|---------------------|
| **DigiCert**     | Enterprise, EV, mTLS           | $200–$1000+/yr      |
| **Sectigo**      | Business websites, wildcard    | $80–$500/yr         |
| **GlobalSign**   | Enterprise, IoT, mTLS          | Custom pricing      |
| **Entrust**      | Government, banking            | Enterprise pricing  |

### For mTLS (Client Certs)

| Option                      | How                                           |
|-----------------------------|-----------------------------------------------|
| Internal CA (self-signed)   | `openssl` or `cfssl` — free, full control     |
| AWS Private CA              | Managed CA for internal services              |
| HashiCorp Vault PKI         | Dynamic cert generation for microservices     |
| Cloudflare for Teams        | mTLS for Zero Trust access                    |
| Istio / Linkerd             | Automatic mTLS in Kubernetes                  |

---

## How to Get a TLS Certificate (Step by Step)

### Option 1: Let's Encrypt (Free, Automated)

```bash
# Install Certbot
sudo apt install certbot

# Get certificate for your domain
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renews every 90 days
```

### Option 2: Generate Self-Signed (Dev/Internal)

```bash
# Generate private key + self-signed cert
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"
```

### Option 3: mTLS Setup with OpenSSL

```bash
# Step 1: Create your own CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -days 3650

# Step 2: Create server cert signed by your CA
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -out server.crt

# Step 3: Create client cert signed by same CA
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -out client.crt
```

---

## mTLS in .NET (C# Example)

```csharp
// Server: Require client certificate
builder.WebHost.ConfigureKestrel(options =>
{
    options.ConfigureHttpsDefaults(https =>
    {
        https.ClientCertificateMode = ClientCertificateMode.RequireCertificate;
        https.ClientCertificateValidation = (cert, chain, errors) =>
        {
            // Validate client cert against your CA
            return cert.Issuer == "CN=MyInternalCA";
        };
    });
});

// Client: Send client certificate
var handler = new HttpClientHandler();
handler.ClientCertificates.Add(
    new X509Certificate2("client.pfx", "password")
);
var client = new HttpClient(handler);
var response = await client.GetAsync("https://api.internal/secure");
```

---

## Certificate Lifecycle

```
[Generate Key Pair]
        ↓
[Create CSR (Certificate Signing Request)]
        ↓
[Submit to CA for signing]
        ↓
[CA verifies identity]
        ↓
[CA issues signed Certificate]
        ↓
[Install on server]
        ↓
[Monitor expiry → Renew before expiry]
        ↓
[Revoke if compromised → CRL / OCSP]
```

---

## Common Certificate Formats

| Format       | Extension          | Used By                          |
|--------------|--------------------|----------------------------------|
| PEM          | `.pem`, `.crt`     | Linux, Nginx, Apache             |
| PFX/PKCS12   | `.pfx`, `.p12`     | Windows, IIS, .NET               |
| DER          | `.der`             | Java, binary format              |
| JKS          | `.jks`             | Java KeyStore                    |

```bash
# Convert PEM to PFX (.NET friendly)
openssl pkcs12 -export -out cert.pfx \
  -inkey server.key -in server.crt -certfile ca.crt
```

---

## Key Terms Cheat Sheet

| Term             | Meaning                                              |
|------------------|------------------------------------------------------|
| **CA**           | Certificate Authority — trusted issuer               |
| **CSR**          | Certificate Signing Request — sent to CA             |
| **Private Key**  | Never shared, used to decrypt / sign                 |
| **Public Key**   | Shared openly, used to encrypt / verify              |
| **Handshake**    | Negotiation process to establish TLS session         |
| **Cipher Suite** | Algorithm combo used for encryption                  |
| **OCSP**         | Online check if a cert is revoked                    |
| **CRL**          | List of revoked certificates                         |
| **SNI**          | Server Name Indication — multiple certs on one IP    |
| **PKI**          | Public Key Infrastructure — the whole system         |

---

## When to Use What?

| Situation                              | Use                           |
|----------------------------------------|-------------------------------|
| Public website / blog                  | TLS (Let's Encrypt)           |
| Public API                             | TLS (Let's Encrypt / ACM)     |
| Microservices inside Kubernetes        | mTLS (Istio/Linkerd)          |
| B2B partner API                        | mTLS (DigiCert / Internal CA) |
| Internal tools / intranet              | TLS (self-signed or private CA)|
| Banking / fintech / healthcare API     | mTLS + EV cert                |
| IoT device ↔ cloud                    | mTLS (client cert per device) |
| Zero Trust network access              | mTLS (Cloudflare / Okta)      |

---

## Summary

```
TLS  → Server proves identity to Client     (1-way)
mTLS → Server AND Client prove identity     (2-way)

Free certs  → Let's Encrypt, AWS ACM, Cloudflare
Paid certs  → DigiCert, Sectigo, GlobalSign
mTLS certs  → Internal CA (openssl), AWS Private CA, Vault

Formats → .pem (Linux) | .pfx (Windows/.NET) | .jks (Java)
```
