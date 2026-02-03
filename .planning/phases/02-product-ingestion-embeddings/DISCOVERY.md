# Phase 2 Discovery: Product Ingestion & Embeddings

**Discovery Level:** 2 (Standard Research)
**Date:** 2026-02-03

## Research Topics

### 1. FashionSigLIP Embedding Generation

**Source:** [Marqo/marqo-fashionSigLIP on Hugging Face](https://huggingface.co/Marqo/marqo-fashionSigLIP)

**Key Findings:**
- Model: `Marqo/marqo-fashionSigLIP` - fine-tuned from ViT-B-16-SigLIP
- Output: 768-dimensional embeddings, normalized for cosine similarity
- License: Apache 2.0 (safe for commercial use)
- Performance: +57% MRR improvement over FashionCLIP 2.0

**Usage Pattern (Selected):**
```python
from transformers import AutoModel, AutoProcessor

model = AutoModel.from_pretrained('Marqo/marqo-fashionSigLIP', trust_remote_code=True)
processor = AutoProcessor.from_pretrained('Marqo/marqo-fashionSigLIP', trust_remote_code=True)

with torch.no_grad():
    inputs = processor(images=[image], return_tensors="pt")
    features = model.get_image_features(inputs['pixel_values'], normalize=True)
    embedding = features[0].tolist()  # 768-dim vector
```

**Alternative (open_clip):** Also supported but transformers is more straightforward.

**Model Management Decision:**
- Load at FastAPI startup as singleton
- Store in `app.state.embedding_service`
- Semaphore limit (4 concurrent) for CPU inference per PROJECT.md
- Memory footprint: ~500-600MB

### 2. WooCommerce REST API

**Source:** [WooCommerce REST API Documentation](https://woocommerce.github.io/woocommerce-rest-api-docs/)

**Key Findings:**
- API Version: v3 (endpoint: `/wp-json/wc/v3`)
- Authentication: Basic Auth with consumer key/secret
- HTTPS: Required for production
- Rate Limiting: Optional, disabled by default on most stores

**Pagination:**
- `page` and `per_page` parameters
- Max `per_page`: 100
- Total count in `X-WP-Total` response header

**Product Fields Used:**
- id, name, description, price, regular_price, sale_price
- images (array of {src, alt})
- permalink, status, stock_status

### 3. Image Quality Gate (Blur Detection)

**Source:** [PyImageSearch - Blur Detection with OpenCV](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/)

**Method: Laplacian Variance**
```python
variance = cv2.Laplacian(gray_image, cv2.CV_64F).var()
```

**Interpretation:**
- Low variance (< threshold) = blurry
- High variance (> threshold) = sharp

**Threshold Selection:**
- Default: 100.0
- Range varies by dataset (50-150 typical)
- Normalize image size before check for consistent scores

**Additional Validations (from PROJECT.md):**
- Minimum dimension: 400px
- File size: 50KB - 10MB

### 4. Qdrant Async Client

**Source:** [Qdrant Python Client Documentation](https://python-client.qdrant.tech/)

**Key Findings:**
- Full async support since v1.6.1
- Use `AsyncQdrantClient` for FastAPI integration
- Collection config: `VectorParams(size=768, distance=Distance.COSINE)`

**Usage Pattern:**
```python
from qdrant_client import AsyncQdrantClient, models

client = AsyncQdrantClient(url="http://localhost:6333")

await client.create_collection(
    collection_name="products",
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
)

await client.upsert(
    collection_name="products",
    points=[models.PointStruct(id="uuid", vector=[...], payload={...})]
)
```

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| transformers over open_clip | More straightforward API, better documentation |
| Startup singleton for model | Avoid per-request load time (~5-10s), matches PROJECT.md semaphore pattern |
| Laplacian threshold = 100 | Standard default, adjustable per dataset |
| AsyncQdrantClient | Native FastAPI async integration |
| Unsplash for bootstrap images | Free, high-quality, allows hotlinking |

## Don't Hand-Roll

- **Embedding generation** - Use transformers library, not custom CLIP implementation
- **Blur detection** - Use OpenCV Laplacian, not custom edge detection
- **S3 operations** - Use aioboto3 (already in place from Phase 1)

## References

- [Marqo FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP)
- [WooCommerce REST API Docs](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [Qdrant Python Client](https://python-client.qdrant.tech/)
- [PyImageSearch Blur Detection](https://pyimagesearch.com/2015/09/07/blur-detection-with-opencv/)
