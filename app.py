# Python 3.11
from flask import Flask, render_template, request, send_file
import os
import re
from collections import Counter
from gtts import gTTS
import tinify
from werkzeug.utils import secure_filename
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

app = Flask(__name__)

OUTPUT_FOLDER = "outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

tinify.key = "jMFKft9K8kv6pT3J7GDzWmgqT9YnLzw8"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- RESUME ----------------
@app.route("/resume", methods=["GET", "POST"])
def resume():
    if request.method == "POST":
        return render_template("resume_preview.html", data=request.form)
    return render_template("resume.html")

@app.route("/download-resume", methods=["POST"])
def download_resume():
    name = request.form["name"]
    file_path = os.path.join(OUTPUT_FOLDER, f"{name}.pdf")

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph(f"<font size=20 color='#1e3a8a'><b>{name}</b></font>", styles['Title']))
    content.append(Spacer(1, 10))

    contact = f"{request.form['email']} | {request.form['phone']} | {request.form['linkedin']}"
    content.append(Paragraph(contact, styles['Normal']))
    content.append(Spacer(1, 15))

    def section(title, text):
        content.append(Paragraph(f"<font size=14 color='#2563eb'><b>{title}</b></font>", styles['Heading2']))
        content.append(Spacer(1, 5))
        content.append(Paragraph(text, styles['Normal']))
        content.append(Spacer(1, 12))

    section("Skills", request.form["skills"])
    section("Education", request.form["education"])
    section("Experience", request.form["experience"])

    doc.build(content)
    return send_file(file_path, as_attachment=True)

# ---------------- SUMMARIZER ----------------
@app.route("/summarizer", methods=["GET", "POST"])
def summarizer():
    summary = ""
    if request.method == "POST":
        text = request.form["text"]
        text = re.sub(r'[^a-zA-Z0-9. ]', '', text)
        words = text.lower().split()
        freq = Counter(words)
        sentences = text.split(".")
        scores = {}

        for sentence in sentences:
            for word in sentence.lower().split():
                if word in freq:
                    scores[sentence] = scores.get(sentence, 0) + freq[word]

        best = sorted(scores, key=scores.get, reverse=True)[:3]
        summary = ". ".join(best)

    return render_template("summarizer.html", summary=summary)

# ---------------- TEXT TO SPEECH ----------------
@app.route("/pdf-to-speech", methods=["GET", "POST"])
def pdf_to_speech():
    if request.method == "POST":
        text = request.form["text"]
        tts = gTTS(text=text, lang='en')
        path = os.path.join(OUTPUT_FOLDER, "audio.mp3")
        tts.save(path)
        return render_template("pdf_speech.html", ready=True)
    return render_template("pdf_speech.html", ready=False)

@app.route("/download-audio")
def download_audio():
    return send_file(os.path.join(OUTPUT_FOLDER, "audio.mp3"), as_attachment=True)

# ---------------- IMAGE COMPRESSOR ----------------
@app.route("/image-compressor", methods=["GET", "POST"])
def image_compressor():
    file_url = None
    if request.method == "POST":
        file = request.files["image"]
        filename = secure_filename(file.filename)

        input_path = os.path.join(OUTPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, "compressed_" + filename)

        file.save(input_path)
        tinify.from_file(input_path).to_file(output_path)

        file_url = "/download/" + os.path.basename(output_path)

    return render_template("image_compressor.html", file=file_url)

@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

# ---------------- PDF MERGE ----------------
@app.route("/merge-pdf", methods=["GET", "POST"])
def merge_pdf():
    if request.method == "POST":
        files = request.files.getlist("pdfs")
        merger = PdfMerger()

        for file in files:
            path = os.path.join(OUTPUT_FOLDER, secure_filename(file.filename))
            file.save(path)
            merger.append(path)

        output_path = os.path.join(OUTPUT_FOLDER, "merged.pdf")
        merger.write(output_path)
        merger.close()

        return send_file(output_path, as_attachment=True)

    return render_template("merge_pdf.html")

# ---------------- PDF SPLIT ----------------
@app.route("/split-pdf", methods=["GET", "POST"])
def split_pdf():
    if request.method == "POST":
        file = request.files["pdf"]
        filename = secure_filename(file.filename)
        input_path = os.path.join(OUTPUT_FOLDER, filename)
        file.save(input_path)

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        output_path = os.path.join(OUTPUT_FOLDER, "split_output.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

        return send_file(output_path, as_attachment=True)

    return render_template("split_pdf.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)