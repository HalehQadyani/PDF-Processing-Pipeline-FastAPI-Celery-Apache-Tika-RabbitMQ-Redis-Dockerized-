import os
import requests
from celery import shared_task
from .utils import redis_client

TIKA_URL = os.environ.get("TIKA_URL", "http://tika:9998")

@shared_task(bind=True, name="parse_pdf")
def parse_pdf(self, file_path: str, filename: str | None = None) -> str:
    """Parse a PDF using Apache Tika and store the result in Redis.

    Steps:
      - Read the file at `file_path` (shared volume)
      - PUT it to `${TIKA_URL}/tika` with `Accept: text/plain`
      - Save plain text result to Redis under key `task_result:{task_id}`
      - Return the text (also stored by Celery in its backend)
    """
    task_id = self.request.id

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Uploaded file not found: {file_path}")

    with open(file_path, "rb") as f:
        resp = requests.put(
            f"{TIKA_URL}/tika",
            data=f, 
            headers={"Accept": "text/plain"},
            timeout=300,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"Tika extraction failed: {resp.status_code} - {resp.text[:500]}")

    text = resp.text

    key = f"task_result:{task_id}"
    redis_client.set(key, text)
    redis_client.expire(key, 7 * 24 * 3600)

    return text