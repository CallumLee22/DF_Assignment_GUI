import os
from dotenv import load_dotenv
from supabase import create_client
from flask import Flask, render_template
from matplotlib import pyplot as plt

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
    all_machines = supabase.table("Machines").select("user_id", "specification_id").execute().data

    user_info = []

    for name in all_users:
        user_info.append(
            {
                "user_id": name["user_id"],
                "full_name": name["first_name"] + " " + name["last_name"],
                "machines": []
            }
        )
    
    for user in user_info:
        for machine in all_machines:
            if machine["user_id"] == user["user_id"]:
                user["machines"].append(machine["specification_id"])

    for user in user_info:
        if len(user["machines"]) != 0:
            cpus = 0
            gpus = 0
            ram_gb = 0
            for machine in user["machines"]:
                spec = supabase.table("Specifications").select("cpus", "gpus", "ram_gb").eq("specification_id", machine).execute().data[0]

                cpus += int(spec["cpus"])
                gpus += int(spec["gpus"])
                ram_gb += int(spec["ram_gb"])

            fig, ax = plt.subplots()

            components = ['CPUs', 'GPUs', 'RAM']
            counts = [cpus, gpus, ram_gb]
            bar_colors = ['tab:red', 'tab:blue', 'tab:green']

            ax.bar(components, counts, color=bar_colors)

            ax.set_xlabel('Component')
            ax.set_ylabel('Number Being Used')
            ax.set_title('Component Usage')

            plt.savefig(f"static/{user['full_name']}.png")

    return render_template("users.jinja", user_info=user_info)


@app.route("/groups")
def groups():
    groups = supabase.table("Groups").select("group_id", "name").execute().data

    return render_template("groups.jinja", groups=groups)


@app.route("/departments")
def departments():
    departments = supabase.table("Departments").select("department_id", "name").execute().data

    return render_template("departments.jinja", departments=departments)


if __name__ == "__main__":
    app.run()
