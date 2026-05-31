from pathlib import Path


UPLOAD_ROOT = Path("data/uploads")
MAX_FILENAME_LENGTH = 80


def get_file_extension(filename):
    suffix = Path(filename).suffix.lower()
    return suffix if suffix else ""


def make_safe_filename(filename):
    name = Path(filename).stem.strip()
    extension = get_file_extension(filename)

    for char in [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|", "\n", "\r", "\t"]:
        name = name.replace(char, "-")

    while "--" in name:
        name = name.replace("--", "-")

    name = name.strip("-") or "uploaded-file"

    if len(name) > MAX_FILENAME_LENGTH:
        name = name[:MAX_FILENAME_LENGTH].rstrip("-")

    return f"{name}{extension}"


def save_uploaded_file(uploaded_file, thread_id, asset_id):
    thread_dir = UPLOAD_ROOT / thread_id
    thread_dir.mkdir(parents=True, exist_ok=True)

    safe_name = make_safe_filename(uploaded_file.name)

    # Keep the physical filename short to avoid Windows path-length issues.
    extension = get_file_extension(safe_name)
    file_path = thread_dir / f"{asset_id}{extension}"

    # Extra safety in case parent dirs were removed between reruns.
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return str(file_path)