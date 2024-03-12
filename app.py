import os
from dotenv import load_dotenv
from supabase import create_client
from flask import Flask, render_template
from matplotlib import pyplot as plt
from cachetools import cached, TTLCache

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
@cached(cache=TTLCache(maxsize=1, ttl=30))
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
@cached(cache=TTLCache(maxsize=1, ttl=30))
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
@cached(cache=TTLCache(maxsize=1, ttl=30))
def departments():
    all_departments = supabase.table("Departments").select("department_id", "name").execute().data
    all_machines = supabase.table("Machines").select("user_id", "specification_id").execute().data
    all_users = supabase.table("Users").select("user_id", "group_id").execute().data
    all_groups = supabase.table("Groups").select("group_id", "department_id").execute().data
    all_specifications = supabase.table("Specifications").select("*").execute().data
    
    dep_names = []
    dep_groups = []

    for department in all_departments:
        dep_names.append(department["name"])

    for department in all_departments:
        groups_in_dep = supabase.table("Groups").select("group_id").eq("department_id", department["department_id"]).execute().data
        groups = []
        for departments in groups_in_dep:
            groups.append(departments["group_id"])
        dep_groups.append({"dep_name": department["name"], "groups": groups})
    
    users_in_group = []
    for group in all_groups:
        users = []
        for user in all_users:
            if user["group_id"] == group["group_id"]:
                users.append(user["user_id"])
        users_in_group.append({"group_id": group["group_id"], "users": users})

    specs_in_group = []
    for group in users_in_group:
        specs = []
        for machine in all_machines:
            if machine["user_id"] in group["users"]:
                specs.append(machine["specification_id"])
        specs_in_group.append({"group_id": group["group_id"], "specifications": specs})

    group_total_usage = []
    for group in specs_in_group:
        ram = 0
        cpus = 0
        gpus = 0
        for specs in group["specifications"]:
            for spec in all_specifications:
                if spec["specification_id"] == specs:
                    ram += spec["ram_gb"]
                    cpus += spec["cpus"]
                    gpus += spec["gpus"]
        group_total_usage.append({"group_id": group["group_id"], "ram": ram, "cpus": cpus, "gpus": gpus})

    groups_in_dep = []
    for dep in all_departments:
        groups = []
        for group in all_groups:
            if group["department_id"] == dep["department_id"]:
                groups.append(group["group_id"])
        groups_in_dep.append({"department_id": dep["department_id"], "groups": groups})

    dep_total_usage = []
    for dep in groups_in_dep:
        dep_total_usage.append({"department_id": dep["department_id"], "ram": 0, "cpus": 0, "gpus": 0})
        for group in group_total_usage:
            if group["group_id"] in dep["groups"]:
                dep_total_usage[dep["department_id"] - 1]["ram"] += group["ram"]
                dep_total_usage[dep["department_id"] - 1]["cpus"] += group["cpus"]
                dep_total_usage[dep["department_id"] - 1]["gpus"] += group["gpus"]

    fig, ax = plt.subplots()

    counts = []
    for dep in dep_total_usage:
        counts.append(dep["cpus"])

    if len(counts) == 0:
        for name in dep_names:
            counts.append(0)

    ax.barh(dep_names, counts)

    ax.invert_yaxis()

    ax.set_xlabel('Department')
    ax.set_ylabel('CPUs Being Used')
    ax.set_title('CPU Usage')

    plt.savefig("static/departments_cpu.png", bbox_inches='tight')

    fig, ax = plt.subplots()

    counts = []
    for dep in dep_total_usage:
        counts.append(dep["gpus"])

    if len(counts) == 0:
        for name in dep_names:
            counts.append(0)

    ax.barh(dep_names, counts)

    ax.set_xlabel('Department')
    ax.set_ylabel('GPUs Being Used')
    ax.set_title('GPU Usage')

    plt.savefig("static/departments_gpu.png", bbox_inches='tight')

    fig, ax = plt.subplots()

    counts = []
    for dep in dep_total_usage:
        counts.append(dep["ram"])

    if len(counts) == 0:
        for name in dep_names:
            counts.append(0)

    ax.barh(dep_names, counts)

    ax.set_xlabel('Department')
    ax.set_ylabel('RAM (Gb) Being Used')
    ax.set_title('RAM Usage')

    plt.savefig("static/departments_ram.png", bbox_inches='tight')

    return render_template("departments.jinja", departments=all_departments)


if __name__ == "__main__":
    app.run()
