# Starfell Labs

A lightweight, self-hosted dataset hub (HuggingFace/Kaggle-style MVP) built for students to **discover, preview, and download datasets** for R assignments and research.

Built by **Mark Chweya**.

## Features (MVP)
- Browse dataset catalog (title, description, tags)
- Dataset detail page with schema + sample preview
- Download datasets by version
- Simple admin upload endpoint (no auth in MVP)

## Tech Stack
- **FastAPI** (backend)
- **Jinja2** (simple UI templates)
- **Pandas** (CSV/Parquet preview)
- **Local storage + JSON catalog** (upgrade to SQLite/S3 later)

## Quickstart

### 1) Create a virtual environment
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
# source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:
- http://127.0.0.1:8000

## Upload a dataset (admin MVP)
Upload a CSV or Parquet file using curl:

```bash
curl -X POST "http://127.0.0.1:8000/admin/upload" \
  -F "title=USIU Sample Survey Data" \
  -F "description=Synthetic student survey dataset for R practice." \
  -F "tags=usiu, survey, r, synthetic" \
  -F "version=1.0.0" \
  -F "file=@./your_dataset.csv"
```

Then refresh the homepage to see the dataset.

## Notes
- This MVP stores metadata in `backend/datasets_storage/_index.json`.
- For public deployment, add an admin key + rate limits, and move storage to S3/MinIO.

## License
MIT
