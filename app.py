from flask import Flask, request, jsonify, render_template, redirect, url_for
from services.vector_store import add_paper_to_index, search_all
import os

from werkzeug.utils import secure_filename

import data_manager as dm
from models import db
from services.pdf import extract_text
from dotenv import load_dotenv
import faiss
import os

load_dotenv()


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

dm.init_db(app)


# ---------- HOME (PAPERS UI) ----------

@app.route("/debug")
def debug_view():
    papers = dm.get_all_papers()
    threads = dm.get_threads()

    thread_messages = {
        t.id: dm.get_messages(t.id)
        for t in threads
    }

    return render_template(
        "debug.html",
        papers=papers,
        threads=threads,
        thread_messages=thread_messages,
    )


@app.route("/")
def home():
    papers = dm.get_all_papers()
    return render_template("index.html", papers=papers)


@app.route("/upload", methods=["POST"])
def upload_paper_html():
    file = request.files["file"]

    if not file or file.filename == "":
        return "No file uploaded", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    text = extract_text(filepath)

    paper_id = dm.create_paper(filename, text)

    add_paper_to_index(paper_id, filename, text)

    return redirect(url_for("home"))


@app.route("/papers/view/<int:paper_id>")
def view_paper_html(paper_id):
    p = dm.get_paper(paper_id)
    return render_template("paper_detail.html", paper=p)


@app.route("/papers/delete/<int:paper_id>", methods=["POST"])
def delete_paper_html(paper_id):
    dm.delete_paper(paper_id)
    return redirect(url_for("home"))


@app.route("/papers/edit/<int:paper_id>", methods=["GET", "POST"])
def edit_paper_html(paper_id):
    p = dm.get_paper(paper_id)

    if request.method == "POST":
        new_name = request.form.get("filename")
        dm.update_paper(paper_id, new_name)
        return redirect(url_for("home"))

    return render_template("edit_paper.html", paper=p)




@app.route("/chat")
def chat_home():
    threads = dm.get_threads()
    return render_template("chat.html", threads=threads)


@app.route("/chat/create", methods=["POST"])
def create_thread_html():
    name = request.form.get("name", "New Thread")
    thread_id = dm.create_thread(name=name)
    return redirect(url_for("chat_thread", thread_id=thread_id))


@app.route("/chat/<int:thread_id>", methods=["GET", "POST"])
def chat_thread(thread_id):
    if request.method == "POST":
        message = request.form.get("message")
        dm.add_message(thread_id, "user", message)

    messages = dm.get_messages(thread_id)

    return render_template(
        "chat_thread.html",
        thread_id=thread_id,
        messages=messages,
    )



@app.route("/search", methods=["GET", "POST"])
def search_all_papers():
    if request.method == "POST":
        query = request.form.get("query")
        results = search_all(query)
    else:
        results = []
        query = ""

    return render_template(
        "search_results.html",
        results=results,
        query=query,
    )

@app.route("/papers", methods=["GET"])
def get_papers():
    papers = dm.get_all_papers()
    return jsonify(
        [{"id": p.id, "filename": p.filename} for p in papers]
    )



if __name__ == "__main__":
    app.run(debug=True)