import os
from dotenv import load_dotenv
from supabase import create_client
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
    all_users = (
        supabase.table("Users")
        .select("user_id", "first_name", "last_name")
        .execute()
        .data
    )
    user_names = []

    for name in all_users:
        user_names.append(
            {
                "user_id": name["user_id"],
                "full_name": name["first_name"] + " " + name["last_name"],
            }
        )

    return render_template("users.jinja", user_names=user_names)


@app.route("/groups")
def groups():
    all_groups = supabase.table("Groups").select("*").execute().data
    names = []

    for name in all_groups:
        names.append(name["name"])

    return render_template("groups.jinja", names=names)


@app.route("/departments")
def departments():
    all_users = supabase.table("Departments").select("*").execute().data
    names = []

    for name in all_users:
        names.append(name["name"])

    return render_template("departments.jinja", names=names)


if __name__ == "__main__":
    app.run()
