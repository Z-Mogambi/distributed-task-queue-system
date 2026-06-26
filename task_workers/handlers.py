import os
import time
import requests
import resend
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import anthropic


# ---------------------------------------------------------------------------
# Email — real delivery via Resend
# ---------------------------------------------------------------------------

def handle_email(payload):
    """Send a real email using the Resend API."""
    to = payload.get("to")
    subject = payload.get("subject", "(no subject)")
    body = payload.get("body", "")

    if not to:
        raise ValueError("Missing 'to' field in email payload")

    resend.api_key = os.environ["RESEND_API_KEY"]

    response = resend.Emails.send({
        "from": "Task Queue <onboarding@resend.dev>",
        "to": [to],
        "subject": subject,
        "text": body,
    })

    return {
        "status": "sent",
        "message_id": response["id"],
        "to": to,
        "timestamp": int(time.time()),
    }


# ---------------------------------------------------------------------------
# Image processing — real resize + compress via Pillow
# ---------------------------------------------------------------------------

def handle_image_processing(payload):
    """Download an image, apply operations (resize, grayscale, compress), return stats."""
    image_url = payload.get("image_url")
    operations = payload.get("operations", ["resize"])
    max_width = payload.get("max_width", 800)

    if not image_url:
        raise ValueError("Missing 'image_url' in image_processing payload")

    print(f"Downloading image from {image_url}...")
    response = requests.get(image_url, timeout=15)
    response.raise_for_status()

    original_size_kb = len(response.content) / 1024
    img = Image.open(BytesIO(response.content)).convert("RGB")
    original_dimensions = img.size

    if "resize" in operations:
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

    if "grayscale" in operations:
        img = img.convert("L").convert("RGB")

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"processed_{int(time.time())}.jpg"
    output_path = os.path.join(output_dir, output_filename)

    quality = 75 if "compress" in operations else 95
    img.save(output_path, "JPEG", quality=quality, optimize=True)

    processed_size_kb = os.path.getsize(output_path) / 1024

    return {
        "status": "processed",
        "original_dimensions": original_dimensions,
        "processed_dimensions": img.size,
        "original_size_kb": round(original_size_kb, 2),
        "processed_size_kb": round(processed_size_kb, 2),
        "size_reduction_pct": round((1 - processed_size_kb / original_size_kb) * 100, 1),
        "operations_applied": operations,
        "output_path": output_path,
    }


# ---------------------------------------------------------------------------
# Calculation — real math, unchanged
# ---------------------------------------------------------------------------

def handle_calculation(payload):
    """Compute sum, average, min, max of a list of numbers."""
    numbers = payload.get("numbers", [])
    if not numbers:
        return {"sum": 0, "average": 0, "min": None, "max": None}
    return {
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
    }


# ---------------------------------------------------------------------------
# Document summary — fetch URL, extract text, summarize with Claude
# ---------------------------------------------------------------------------

def handle_document_summary(payload):
    """Download a URL, extract readable text, and summarize it with Claude."""
    url = payload.get("url")
    if not url:
        raise ValueError("Missing 'url' in document_summary payload")

    print(f"Fetching document from {url}...")
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "html" in content_type:
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    else:
        text = response.text

    # Keep the first ~3000 words to stay within a reasonable token budget
    words = text.split()
    truncated_text = " ".join(words[:3000])
    was_truncated = len(words) > 3000

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Summarize the following document in 3-5 concise bullet points:\n\n{truncated_text}"
                ),
            }
        ],
    )

    summary = message.content[0].text

    return {
        "status": "summarized",
        "url": url,
        "summary": summary,
        "word_count": len(words),
        "was_truncated": was_truncated,
        "model": message.model,
        "timestamp": int(time.time()),
    }


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def process_job(job):
    """Route a job to its handler by type."""
    job_type = job.get("type")
    if not job_type:
        raise ValueError("Job type is missing from job dictionary")

    handler = JOB_HANDLERS.get(job_type)
    if handler is None:
        raise ValueError(f"No handler for job type: '{job_type}'")

    return handler(job.get("payload", {}))


JOB_HANDLERS = {
    "email": handle_email,
    "image_processing": handle_image_processing,
    "calculation": handle_calculation,
    "document_summary": handle_document_summary,
}
