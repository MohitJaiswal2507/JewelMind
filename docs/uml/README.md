# UML & Architectural Models Specification

> **Document Version:** 1.1.0 (Phase 1 Foundation)  
> **Status:** Architectural Models & Future Diagram Registry  

---

## 1. Planned UML Diagram Suite

### 1.1 Use Case Diagram
- **Actors:** Jewellery Designer (User), Workshop Artisan, Production Manager, AI Worker.
- **Key Use Cases:**
  - Authenticate & Manage Profile
  - Create Jewellery Design & Upload Sketch
  - Generate Photorealistic AI Render
  - Inspect Detected Components & Adjust Counts
  - View AI Material, Cost, Labor, and Wastage Predictions
  - Assess Manufacturability Score & Risk Flags
  - Create Production Order & Set Priority/Deadline
  - Execute OR-Tools Schedule Optimization
  - View Workshop Gantt Timeline

### 1.2 Entity Class Diagram
- **Data Models:**
  - `User` $\leftrightarrow$ `Design`
  - `Design` $\leftrightarrow$ `Sketch`
  - `Design` $\leftrightarrow$ `AIJob` $\leftrightarrow$ `AIResult`
  - `Design` $\leftrightarrow$ `JewelleryComponent`
  - `Design` $\leftrightarrow$ `Prediction`
  - `Design` $\leftrightarrow$ `ProductionOrder` $\leftrightarrow$ `ProductionSchedule`

### 1.3 Sequence Diagrams
1. **Asynchronous Sketch-to-Render Flow:** Client $\rightarrow$ API $\rightarrow$ Supabase Storage $\rightarrow$ AI Job Queue $\rightarrow$ RTX 4060 Worker $\rightarrow$ Client Poll.
2. **Predictive Analytics & Component Detection:** Client $\rightarrow$ API $\rightarrow$ YOLO Detection $\rightarrow$ Feature Vector Extraction $\rightarrow$ XGBoost Inference $\rightarrow$ Response.
3. **Constraint-Based Schedule Optimization:** Production Manager $\rightarrow$ API $\rightarrow$ OR-Tools CP-SAT Solver $\rightarrow$ Schedule Persistence $\rightarrow$ Frontend Timeline.

### 1.4 Deployment Diagram
- **Web Tier:** Cloudflare Pages (React 19 SPA).
- **Application Tier:** FastAPI (Python 3.13) + Alembic + SQLAlchemy.
- **Persistence Tier:** Supabase PostgreSQL + S3-Compatible Storage.
- **Compute Tier:** Local NVIDIA RTX 4060 GPU Worker + Optional Hugging Face ZeroGPU.
