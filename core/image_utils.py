import os
import hashlib
from PIL import Image
from PIL.ExifTags import TAGS

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")

CATEGORY_RULES = {
    "Screenshots": ["screenshot", "screen shot"],
    "Camera": ["img_", "dcim", "camera"],
    "Downloaded": ["download"],
    "Wallpapers": ["wallpaper"],
}


def categorize(file_path):
    lowered = file_path.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(k in lowered for k in keywords):
            return category
    return "Others"


def file_hash(path, chunk_size=65536):
    """Fast hash-based duplicate detection (lightweight, not perceptual AI)."""
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


def scan_images(root_path, progress_callback=None):
    """One-time manual scan with progress — not continuous background."""
    all_files = []
    for dirpath, _, filenames in os.walk(root_path, onerror=lambda e: None):
        for f in filenames:
            if f.lower().endswith(IMAGE_EXTS):
                all_files.append(os.path.join(dirpath, f))

    results = []
    hash_map = {}
    total = len(all_files) or 1

    for idx, path in enumerate(all_files):
        h = file_hash(path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        entry = {
            "path": path,
            "hash": h,
            "size": size,
            "category": categorize(path),
        }
        results.append(entry)
        if h:
            hash_map.setdefault(h, []).append(path)

        if progress_callback:
            progress_callback(int((idx + 1) / total * 100))

    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    return results, duplicates


def get_image_metadata(path):
    """Per-file read only — lightweight."""
    try:
        with Image.open(path) as img:
            info = {"Resolution": f"{img.width}x{img.height}", "Format": img.format}
            exif_data = img._getexif() if hasattr(img, "_getexif") else None
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ("DateTime", "Make", "Model"):
                        info[tag] = value
            return info
    except Exception:
        return {}


def bytes_to_human(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"