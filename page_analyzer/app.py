from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from urllib.parse import urlparse
import validators

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET", "POST"])
def urls():
    if request.method == "POST":
        url = request.form.get("url")
        if not validators.url(url):
            flash("Invalid URL. Please enter a valid URL.", "danger")
            return redirect(url_for("index"))

        normalized_url = urlparse(url).netloc
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO urls (name) VALUES (%s) "
                        "ON CONFLICT (name) DO NOTHING RETURNING id",
                        (normalized_url,),
                    )
                    url_id = cur.fetchone()
                    if url_id:
                        flash("URL added successfully!", "success")
                    else:
                        flash("URL already exists.", "info")
        except Exception as e:
            flash(f"Database error: {e}", "danger")
        return redirect(url_for("urls"))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
            urls = cur.fetchall()
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def show_url(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()
    if not url:
        flash("URL not found.", "danger")
        return redirect(url_for("urls"))
    return render_template("url.html", url=url)
