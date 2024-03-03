import os
from dotenv import load_dotenv
from supabase import create_client, Client
from flask import Flask, render_template

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

app = Flask(__name__)
app.app_context().push()
app.config["SECRET_KEY"] = "secret_key"

@app.route("/")
def index():
    return render_template("index.jinja")

@app.route("/users")
def users():
    return render_template("users.jinja")

@app.route("/groups")
def groups():
    return render_template("groups.jinja")

@app.route("/departments")
def departments():
    return render_template("departments.jinja")

if __name__ == "__main__":
    app.run()
