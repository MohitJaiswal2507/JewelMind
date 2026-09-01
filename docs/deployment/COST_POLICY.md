# Zero-Cost Infrastructure & Deployment Policy (₹0 Budget)

> **Core Principle:** JewelMind is intentionally engineered to operate on a strict **₹0 budget**.

---

## 1. Budget Framework

JewelMind incurs **₹0** in ongoing costs by leveraging:
1. **Developer Hardware for Heavy Compute:** Local NVIDIA RTX 4060 Laptop GPU for deep learning training, diffusion rendering, and model inference.
2. **Generous Cloud Free Tiers:** Free offerings from developer-friendly platforms for hosting, database, and storage.
3. **Open-Source Tooling:** Freely licensed AI architectures (YOLO, Stable Diffusion, ControlNet, XGBoost, OR-Tools).

---

## 2. Infrastructure Breakdown

| Service Area | Zero-Cost Solution | Free Tier Allowance / Capabilities |
| :--- | :--- | :--- |
| **Frontend CDN Hosting** | Cloudflare Pages | Unlimited requests/bandwidth, custom domain support, global edge CDN. |
| **Backend API Server** | Free Tier Cloud Platform (Render / Railway / Koyeb / Fly.io) | Free tier instances suitable for lightweight asynchronous FastAPI API services. |
| **Relational Database** | Supabase PostgreSQL | 500 MB database, unlimited API requests, automatic SSL. |
| **Object Storage** | Supabase Storage | 1 GB file storage for original sketches, rendering outputs, and masks. |
| **Primary AI Compute** | Local RTX 4060 GPU Worker | Unconstrained local GPU computing for training and inference with zero hourly fees. |
| **Secondary Remote AI** | Hugging Face Spaces / ZeroGPU | Free cloud worker for public live demos without local machine dependency. |
| **Code Repository & CI** | GitHub Free | Unlimited public/private repositories, GitHub Actions free minutes. |

---

## 3. Portability & Vendor Independence
Cloud provider free tier policies may evolve. To protect against vendor lock-in:
- Database access uses standard PostgreSQL connectivity.
- Storage interactions use S3-compatible interfaces.
- AI workers connect via standardized REST JSON protocols, allowing them to run on local laptops, secondary machines, or any cloud compute node.
