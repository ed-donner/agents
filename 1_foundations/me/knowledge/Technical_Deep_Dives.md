# Teknik Araştırma ve Deneyimler

## RAG Sistemleri - Optimizasyon Stratejileri

### 1. Chunk Size Optimizasyonu
**Hipotez:** Daha büyük chunk size daha iyi context sağlar.
**Test:** 256, 512, 1024, 2048 token chunk sizes
**Sonuç:** 512 token sweet spot
- 256: Çok fazla fragmentation
- 512: ✅ Optimal balance
- 1024: Noise artıyor, precision düşüyor
- 2048: Performans düşüyor, irrelevant bilgi

**Veri:**
- Dataset: 10K technical documents
- Queries: 500 test questions
- Metric: MRR@10 (Mean Reciprocal Rank)
- Winner: 512 token (MRR: 0.78)

### 2. Embedding Model Karşılaştırması

| Model | Dimensions | Speed | Accuracy | Cost/1M tokens |
|-------|-----------|-------|----------|----------------|
| text-embedding-3-small | 1536 | Fast | 87% | $0.02 |
| text-embedding-3-large | 3072 | Slow | 91% | $0.13 |
| text-embedding-ada-002 | 1536 | Medium | 84% | $0.10 |

**Karar:** text-embedding-3-small kullan, %4 accuracy loss kabul edilebilir maliyet için.

### 3. Reranking Stratejisi
**Problem:** Top-10 semantic search results bazen irrelevant
**Çözüm:** Cross-encoder reranking (ms-marco-MiniLM)

**Sonuçlar:**
- Before reranking: Precision@3 = 0.65
- After reranking: Precision@3 = 0.83
- Latency artışı: +120ms (acceptable)

### 4. Hybrid Search Implementation
**Senaryo:** Semantic + Keyword (BM25) combined

```python
# Reciprocal Rank Fusion (RRF)
def combine_results(semantic_results, keyword_results, k=60):
    scores = {}
    for rank, doc in enumerate(semantic_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    for rank, doc in enumerate(keyword_results):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Sonuç:** %23 NDCG improvement

---

## Kubernetes Production Savaş Alanı

### Resource Limits Best Practices

**Öğrendiklerim:**
1. **Memory limits her zaman set et**
   - Limit yok = Node'u crash edebilir
   - Request = Gerçek kullanım
   - Limit = 2x Request (safety buffer)

2. **CPU limits dikkatli kullan**
   - CPU throttling gizli performance killer
   - Request yeterli, limit gereksiz çoğunlukla
   - Exception: Noisy neighbor senaryoları

3. **Vertical Pod Autoscaler (VPA) kullan**
   - Manuel tuning obsolete
   - VPA recommendations takip et
   - Production'da "updateMode: Off" + manual apply safer

### Network Policy Debugging Çözümleri

**Problem:** Pod-to-pod connectivity intermittent failures
**Root Cause:** NetworkPolicy misconfiguration + CNI bug
**Debug Tools:**
- `kubectl exec -it <pod> -- nc -zv <target-pod-ip> 8080`
- `kubectl describe networkpolicy`
- Cilium Hubble for traffic visibility

**Çözüm:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
  egress:
  - to:
    - podSelector: {}
  - to:  # DNS için
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

### Persistent Volume Failures

**Lesson 1:** StatefulSet + PVC deletion dangerous
- PVC silmeyi unuttun = data loss
- Always backup before scaling down
- Use VolumeClaimTemplates correctly

**Lesson 2:** Storage class performance matters
- gp2 → gp3 migration: %20 cost save, same performance
- io2 for databases, gp3 for everything else
- EBS CSI driver latest version critical (bug fixes)

---

## Terraform IaC Savaş Hikayeleri

### State Management Lessons

**Disaster:** Concurrent runs without locking → state corruption
**Fix:**
```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-prod"
    key            = "global/s3/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"  # CRITICAL
    encrypt        = true
  }
}
```

### Module Versioning Strategy

**Problem:** Breaking changes in modules broke production
**Solution:**
```hcl
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # NOT latest, explicit version
}
```

**Best Practice:**
- Pin major versions
- Test upgrades in staging
- Use Terraform Cloud for better workflow

### Import Existing Resources

**Use Case:** Brownfield → Terraform migration
**Tool:** `terraformer` for bulk import

```bash
terraformer import aws --resources=vpc,subnet,sg --regions=us-east-1
```

**Warning:** Review imported code, cleanup needed

---

## MLOps Pipeline Design

### Model Versioning Strategy

**System:** MLflow + DVC + S3
- Code versioning: Git
- Data versioning: DVC (S3 backend)
- Model versioning: MLflow (artifacts + metadata)
- Experiment tracking: MLflow UI

### Feature Store Implementation

**Problem:** Feature engineering duplicated across teams
**Solution:** Feast feature store on K8s

**Architecture:**
- Offline store: S3 Parquet files
- Online store: Redis cluster
- Registry: PostgreSQL
- SDK: Python client in training/serving code

**Benefits:**
- Feature reuse +300%
- Training/serving skew eliminated
- Faster experimentation (features ready)

### Model Monitoring in Production

**Metrics to Track:**
1. **Data drift:** KS test on input distributions
2. **Model drift:** Prediction distribution over time
3. **Performance:** Accuracy, latency, throughput
4. **Business metrics:** Conversion, revenue impact

**Tools:**
- Evidently AI for drift detection
- Prometheus + Grafana for metrics
- Custom alerting on business KPIs

---

## Genel Öğrenmeler

### Debugging Felsefesi
1. **Reproduce first, fix second**
2. **Simplify the system** (binary search debugging)
3. **Logs are good, metrics are better, traces are best**
4. **Blame the integration, not the component**

### Scalability Principles
1. **Stateless > Stateful** (always)
2. **Async > Sync** (when possible)
3. **Cache aggressively** (but invalidate correctly)
4. **Design for failure** (chaos engineering mindset)

### Cost Optimization Mindset
1. **Measure before optimizing**
2. **Right-sizing > Over-provisioning**
3. **Spot instances where tolerable**
4. **Reserved/Savings Plans for predictable**
5. **Delete unused resources** (sounds obvious, rarely done)
