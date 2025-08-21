import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from celery.result import AsyncResult

from .celery_app import celery_app
from .tasks import parse_pdf
from .utils import UPLOAD_DIR, redis_client

app = FastAPI(title="PDF Tika Parser API", version="1.0.0")


@app.get("/")
async def root():
    return {"service": "pdf-tika-celery", "endpoints": ["/upload", "/status/{task_id}", "/result/{task_id}"]}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
   
    if file.content_type not in ("application/pdf", "application/x-pdf") and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")


    os.makedirs(UPLOAD_DIR, exist_ok=True)

   
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    base, ext = os.path.splitext(save_path)
    counter = 1
    while os.path.exists(save_path):
        save_path = f"{base}_{counter}{ext or '.pdf'}"
        counter += 1

   
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    task = parse_pdf.delay(save_path, file.filename)

    return {"task_id": task.id, "filename": os.path.basename(save_path)}


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    info = {"task_id": task_id, "state": res.state}
    if res.state == "FAILURE":
        info["error"] = str(res.result)
    return JSONResponse(info)


@app.get("/result/{task_id}")
async def get_result(task_id: str):
    key = f"task_result:{task_id}"
    if not redis_client.exists(key):
        res = AsyncResult(task_id, app=celery_app)
        if res.state in ("PENDING", "STARTED", "RETRY"):
            return JSONResponse({"task_id": task_id, "state": res.state, "message": "Result not ready yet"}, status_code=202)
        elif res.state == "FAILURE":
            return JSONResponse({"task_id": task_id, "state": res.state, "error": str(res.result)}, status_code=500)
        else:
            return JSONResponse({"task_id": task_id, "state": res.state, "message": "No result found"}, status_code=404)

    text = redis_client.get(key)
    return JSONResponse({"task_id": task_id, "state": "SUCCESS", "text": text})