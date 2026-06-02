# Signature Detection POC

YOLOv8-based signature detection, enhancement, and verification system.

## Features
- **Signature detection** — YOLOv8 fine-tuned to find signatures, initials, and stamps
- **Quality assessment** — automatic blur/contrast/noise scoring
- **Image enhancement** — OpenCV denoise → CLAHE → unsharp mask for low-quality scans
- **Dataset management** — Kaggle downloader + local review before training
- **Data augmentation** — expands 100 manual samples ~12× for training
- **MinIO storage** — authenticated object storage with presigned URLs
- **REST API** — FastAPI endpoints for integration
- **Dashboard** — Streamlit UI for visual pipeline management

## Project Structure
```
signature-poc/
├── src/
│   ├── dataset/
│   │   ├── kaggle_downloader.py   # Download + preview Kaggle datasets
│   │   └── augmentor.py           # Signature-safe augmentation
│   ├── enhancement/
│   │   └── enhancer.py            # QA scoring + OpenCV enhancement
│   ├── detection/
│   │   ├── detector.py            # YOLOv8 inference wrapper
│   │   └── pipeline.py            # End-to-end orchestrator
│   └── storage/
│       └── minio_client.py        # MinIO upload/download/presigned URLs
├── scripts/
│   ├── setup.py                   # One-shot project setup
│   ├── prepare_data.py            # Augment + train/val/test split
│   ├── train.py                   # Fine-tune YOLOv8
│   └── run_pipeline.py            # CLI inference
├── configs/
│   └── dataset.yaml               # YOLOv8 dataset config
├── api.py                         # FastAPI REST API
├── dashboard.py                   # Streamlit dashboard
├── requirements.txt
└── .env.example
```

## Quick Start

```bash
# 1. Setup
python scripts/setup.py --kaggle-user YOUR_USER --kaggle-key YOUR_KEY

# 2. Get datasets (review manually in data/preview/ before training)
python src/dataset/kaggle_downloader.py --download robinreni/signature-verification-dataset
python src/dataset/kaggle_downloader.py --import-manual /path/to/your/100/images

# 3. Approve after review
python src/dataset/kaggle_downloader.py --approve robinreni/signature-verification-dataset

# 4. Prepare data (augment + split)
python scripts/prepare_data.py

# 5. Train
python scripts/train.py --epochs 100 --device cpu   # or --device 0 for GPU

# 6. Detect signatures
python scripts/run_pipeline.py --image /path/to/form.jpg
python scripts/run_pipeline.py --batch /path/to/forms/

# 7. Start API
python api.py                        # http://localhost:8000/docs

# 8. Start dashboard
streamlit run dashboard.py           # http://localhost:8501
```

## MinIO Setup

```bash
# Start MinIO with Docker
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ':9001'

# Console: http://localhost:9001
```

## Recommended Kaggle Datasets

| Dataset | Images | Notes |
|---------|--------|-------|
| robinreni/signature-verification-dataset | ~1600 | Genuine + forged, best for POC |
| ishaanv/SigNet | ~8000 | Strong benchmark |
| divyanshrai3101/handwritten-signatures | ~500 | Quick start |
| patrickaudriaz/tobacco800 | Varies | Real document forms |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Service health + model status |
| POST | /detect | Full detection report |
| POST | /verify | Quick verified/not verdict |
| GET | /runs | List MinIO stored runs |
| GET | /storage/health | MinIO connection status |
| GET | /docs | Swagger UI |

## Classes

| ID | Name | Description |
|----|------|-------------|
| 0 | signature | Full handwritten signature |
| 1 | initials | Abbreviated initials |
| 2 | stamp | Rubber stamp / seal |
