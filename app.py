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

            ax.barh(components, counts, color=bar_colors)

            ax.set_xlabel('Component')
            ax.set_ylabel('Number Being Used')
            ax.set_title('Component Usage')

            plt.savefig(f"static/{user['full_name']}.png")

    return render_template("users.jinja", user_info=user_info)


@app.route("/groups")
def groups():
    all_machines = supabase.table("Machines").select("user_id", "specification_id").execute().data
    all_users = supabase.table("Users").select("user_id", "group_id").execute().data
    all_groups = supabase.table("Groups").select("group_id", "name").execute().data
    all_specifications = supabase.table("Specifications").select("*").execute().data
    
    group_names = []

    for group in all_groups:
        group_names.append(group["name"])

    group_info = []

    for group in all_groups:
        users = []
        for user in all_users:
            if user["group_id"] == group["group_id"]:
                users.append(user["user_id"])
        group_info.append({"group_id": group["group_id"], "name": group["name"],"users": users, "machines": []})

    for group in group_info:
        machines = []
        for machine in all_machines:
            if machine["user_id"] in group["users"]:
                group["machines"].append(machine["specification_id"])

    for group in group_info:
        cpus = 0
        gpus = 0
        ram_gb = 0
        for machine in group["machines"]:
            spec = supabase.table("Specifications").select("cpus", "gpus", "ram_gb").eq("specification_id", machine).execute().data[0]

            cpus += int(spec["cpus"])
            gpus += int(spec["gpus"])
            ram_gb += int(spec["ram_gb"])

        fig, ax = plt.subplots()

        components = ['CPUs', 'GPUs', 'RAM']
        counts = [cpus, gpus, ram_gb]
        bar_colors = ['tab:red', 'tab:blue', 'tab:green']

        ax.barh(components, counts, color=bar_colors)

        ax.set_xlabel('Component')
        ax.set_ylabel('Number Being Used')
        ax.set_title('Component Usage')

        plt.savefig(f"static/{group['name']}.png")

    return render_template("groups.jinja", groups=all_groups)


@app.route("/departments")
def departments():

    return render_template("departments.jinja", departments=all_departments)


if __name__ == "__main__":
    app.run()
