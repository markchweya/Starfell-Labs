from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import uuid
import pandas as pd

APP_DIR = Path(__file__).resolve().parent
STORAGE_DIR = (APP_DIR.parent / "datasets_storage").resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Starfell Labs", version="0.1.0")

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# MVP index: simple JSON catalog (upgrade to SQLite later)
INDEX_PATH = STORAGE_DIR / "_index.json"
if not INDEX_PATH.exists():
    INDEX_PATH.write_text(json.dumps({"datasets": []}, indent=2), encoding="utf-8")

def load_index():
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))

def save_index(idx):
    INDEX_PATH.write_text(json.dumps(idx, indent=2), encoding="utf-8")

def dataset_dir(dataset_id: str, version: str):
    d = STORAGE_DIR / dataset_id / version
    d.mkdir(parents=True, exist_ok=True)
    return d

def preview_file(path: Path, n: int = 25):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in [".parquet", ".pq"]:
        df = pd.read_parquet(path)
    else:
        raise HTTPException(400, "Only CSV/Parquet supported for preview in this MVP.")
    return df.head(n).to_dict(orient="records"), list(df.columns)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    idx = load_index()
    return templates.TemplateResponse("index.html", {"request": request, "datasets": idx["datasets"]})

@app.get("/datasets/{dataset_id}", response_class=HTMLResponse)
def dataset_page(request: Request, dataset_id: str):
    idx = load_index()
    ds = next((d for d in idx["datasets"] if d["id"] == dataset_id), None)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    latest = ds["versions"][-1]
    file_path = Path(latest["file_path"])
    sample, columns = preview_file(file_path)

    return templates.TemplateResponse(
        "dataset.html",
        {"request": request, "ds": ds, "latest": latest, "columns": columns, "sample": sample}
    )

@app.get("/datasets/{dataset_id}/download/{version}")
def download(dataset_id: str, version: str):
    idx = load_index()
    ds = next((d for d in idx["datasets"] if d["id"] == dataset_id), None)
    if not ds:
        raise HTTPException(404, "Dataset not found")

    ver = next((v for v in ds["versions"] if v["version"] == version), None)
    if not ver:
        raise HTTPException(404, "Version not found")

    path = Path(ver["file_path"])
    if not path.exists():
        raise HTTPException(404, "File missing on server")

    return FileResponse(path, filename=path.name)

@app.post("/admin/upload")
def upload_dataset(
    title: str = Form(...),
    description: str = Form(...),
    tags: str = Form(""),
    version: str = Form("1.0.0"),
    file: UploadFile = File(...)
):
    # MVP: no auth. Add an admin key before public deployment.
    if not file.filename:
        raise HTTPException(400, "No file uploaded")

    dataset_id = str(uuid.uuid4())[:8]
    ds_path = dataset_dir(dataset_id, version)
    out_path = ds_path / file.filename

    with out_path.open("wb") as f:
        f.write(file.file.read())

    metadata = {
        "id": dataset_id,
        "title": title,
        "description": description,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "versions": [{"version": version, "file_name": file.filename, "file_path": str(out_path)}]
    }
    (ds_path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    idx = load_index()
    idx["datasets"].append(metadata)
    save_index(idx)

    return {"ok": True, "id": dataset_id, "version": version}
