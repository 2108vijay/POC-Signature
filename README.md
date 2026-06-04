# Signature Detection POC

YOLOv8-based signature detection and document verification system.
Detects signatures from cheques, forms, and agreements using two ML models.

---

## What It Does

- Accepts a document image (cheque / form / agreement)
- Classifies the document type automatically
- Detects and isolates the signature region
- Stores everything in MinIO object storage
- Returns a structured JSON result

---

## Project Structure
POC-Signature/
│
├── api/                          ← REST API (Your work)
│   ├── routers/
│   │   ├── health.py             # /health, /storage/health
│   │   ├── upload.py             # /upload
│   │   ├── files.py              # /files, /files/{name}, DELETE
│   │   └── detect.py             # /detect — main endpoint
│   ├── src/
│   │   └── storage/
│   │       └── minio_client.py   # MinIO client
│   ├── models/                   # .pt files go here (see Model Files below)
│   ├── dependencies.py           # Shared models + storage instance
│   ├── main.py                   # App entry point
│   ├── .env.example              # Environment variable template
│   └── requirements.txt
│
├── docker/                       ← Docker setup (Your work)
│   ├── docker-compose.yml        # MinIO + API services
│   ├── Dockerfile
│   └── .env.example
│
├── dataset/                      ← Dataset management (Partner's work)
│   ├── configs/
│   │   └── dataset.yaml          # YOLOv8 dataset config
│   └── augmentor.py              # Signature-safe augmentation
│
├── training/                     ← Model training (Partner's work)
│   ├── detector.py               # YOLOv8 inference wrapper
│   ├── enhancer.py               # Image quality + enhancement
│   ├── pipeline.py               # End-to-end orchestrator
│   └── train.py                  # Training script
│
├── .gitignore
└── README.md

---

## Model Files

The `.pt` model files are not included in this repo due to size.

Download from Google Drive: `[share your drive link here]`

Place them in:
api/models/document_classifier.pt
api/models/signature_yolov8_v2.pt

### What each model does

| Model | File | Purpose |
|---|---|---|
| Document Classifier | `document_classifier.pt` | Identifies cheque / form / agreement / others |
| Signature Detector | `signature_yolov8_v2.pt` | Finds and crops the signature region |

---

## Team Contributions

| Member | Repo | Responsible For |
|---|---|---|
| Vijay | POC-Signature | API, Docker, MinIO storage |
| Aiswarya | POC-Signature-Training | Dataset, Training, Model weights |

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/2108vijay/POC-Signature.git
cd POC-Signature
```

### 2. Set up environment
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Start MinIO via Docker
```bash
cd docker
docker-compose up
```

MinIO Console → `http://localhost:9001`

### 4. Download model files
Download both `.pt` files from Google Drive and place in `api/models/`

### 5. Start the API
```bash
cd api
python3 main.py
```

API docs → `http://localhost:8000/docs`

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | API + MinIO status |
| GET | `/storage/health` | MinIO bucket details |
| POST | `/upload` | Upload image to MinIO |
| POST | `/detect` | Classify document + detect signature |
| GET | `/files` | List all stored files |
| GET | `/files/{name}` | Get presigned URL for a file |
| DELETE | `/files/{name}` | Delete a file |
| GET | `/docs` | Swagger UI |

---

## Sample JSON Output

Upload a cheque/form/agreement to `/detect` and get back:

```json
{
  "document": "cheque.jpg",
  "document_type": "cheque",
  "document_confidence": 0.94,
  "signature_found": true,
  "signature_verified": true,
  "total_signatures": 1,
  "detections": [
    {
      "signature_id": 1,
      "confidence": 0.89,
      "verified": true,
      "bounding_box": {
        "x1": 420,
        "y1": 310,
        "x2": 680,
        "y2": 410,
        "width": 260,
        "height": 100
      },
      "crop_url": "http://localhost:9000/..."
    }
  ],
  "stored_as": "uploads/abc123_cheque.jpg"
}
```

---

## Document Types

| Label | Description |
|---|---|
| `cheque` | Bank cheque with MICR line |
| `form` | Filled application or government form |
| `agreement` | Legal document or stamp paper |
| `others` | Unknown document type |

---

## Tech Stack

| Component | Technology |
|---|---|
| Object Detection | YOLOv8 (Ultralytics) |
| Image Enhancement | OpenCV, CLAHE |
| Storage | MinIO |
| API | FastAPI + Uvicorn |
| Containerisation | Docker + Docker Compose |
| Training | Google Colab (T4 GPU) |
