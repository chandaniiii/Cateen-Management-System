import os
import uuid

from werkzeug.utils import secure_filename

from config import Config


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_upload(file):
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        raise ValueError("Invalid file type. Allowed: png, jpg, jpeg, gif, webp")

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)
    return f"/static/images/uploads/{filename}"
