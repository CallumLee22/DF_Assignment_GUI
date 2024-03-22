"""
Web app that shows usage of users, groups and departments
"""

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
    """
    Index page for website
    """
    return render_template("index.jinja")


@app.route("/users")
@cached(cache=TTLCache(maxsize=1, ttl=30))
def users():
    """
    Gets all users' usage
    """
    all_users = (
        supabase.table("Users")
        .select("user_id", "first_name", "last_name")
        .execute()
        .data
    )

    user_info = []

    for name in all_users:
        all_machines = (
            supabase.table("Machines")
            .select("user_id", "specification_id", "state")
            .eq("user_id", name["user_id"]).neq("state", "DELETED")
            .execute().data
        )

        user_info.append(
            {
                "user_id": name["user_id"],
                "full_name": name["first_name"] + " " + name["last_name"],
                "machines": [
                    machine["specification_id"]
                    for machine in all_machines
                    ]
            }
        )

    for user in user_info:
        cpus = 0
        gpus = 0
        ram_gb = 0
        for machine in user["machines"]:
            spec = (
                supabase.table("Specifications")
                .select("cpus", "gpus", "ram_gb")
                .eq("specification_id", machine)
                .execute().data[0]
            )

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
    """
    Gets all usage regarding groups
    """
    all_machines = (
        supabase.table("Machines").select("user_id", "specification_id")
        .neq("state", "DELETED").execute().data
    )
    all_users = supabase.table("Users").select("user_id", "group_id").execute().data
    all_groups = supabase.table("Groups").select("group_id", "name").execute().data

    group_info = []

    for group in all_groups:
        groups_user = []
        for user in all_users:
            if user["group_id"] == group["group_id"]:
                groups_user.append(user["user_id"])
        group_info.append({"name": group["name"],"users": groups_user, "machines": []})

    for group in group_info:
        for machine in all_machines:
            if machine["user_id"] in group["users"]:
                group["machines"].append(machine["specification_id"])

    for group in group_info:
        cpus = 0
        gpus = 0
        ram_gb = 0
        for machine in group["machines"]:
            spec = (
                supabase.table("Specifications")
                .select("cpus", "gpus", "ram_gb")
                .eq("specification_id", machine)
                .execute().data[0]
            )

            cpus += int(spec["cpus"])
            gpus += int(spec["gpus"])
            ram_gb += int(spec["ram_gb"])

        fig, axes = plt.subplots()

        components = ['CPUs', 'GPUs', 'RAM']
        counts = [cpus, gpus, ram_gb]
        bar_colors = ['tab:red', 'tab:blue', 'tab:green']

        axes.barh(components, counts, color=bar_colors)

        axes.set_xlabel('Component')
        axes.set_ylabel('Number Being Used')
        axes.set_title('Component Usage')

        plt.savefig(f"static/{group['name']}.png")

    return render_template("groups.jinja", groups=all_groups)


@app.route("/departments")
@cached(cache=TTLCache(maxsize=1, ttl=30))
def departments():
    """
    Gets all usage regarding departments
    """
    all_departments = (
        {dep["department_id"]: dep["name"]
         for dep in supabase.table("Departments")
         .select("department_id", "name")
         .execute().data}
    )

    dep_total_usage = get_department_info()

    dep_names = [all_departments[name] for name in all_departments.keys()]

    fig, axes = plt.subplots()

    counts = []
    for dep in dep_total_usage:
        counts.append(dep["cpus"])

    if len(counts) == 0:
        for _ in dep_names:
            counts.append(0)

    axes.barh(dep_names, counts)

    axes.invert_yaxis()

    axes.set_xlabel('CPUs Being Used')
    axes.set_ylabel('Department')
    axes.set_title('CPU Usage')

    plt.savefig("static/departments_cpu.png", bbox_inches='tight')

    fig, axes = plt.subplots()

    counts = []
    for dep in dep_total_usage:
        counts.append(dep["gpus"])

    if len(counts) == 0:
        for _ in dep_names:
            counts.append(0)

    axes.barh(dep_names, counts)

    axes.set_xlabel('GPUs Being Used')
    axes.set_ylabel('Department')
    axes.set_title('GPU Usage')

    plt.savefig("static/departments_gpu.png", bbox_inches='tight')

    fig, axes = plt.subplots()

    counts = []
    for dep in dep_total_usage:
        counts.append(dep["ram"])

    if len(counts) == 0:
        for _ in dep_names:
            counts.append(0)

    axes.barh(dep_names, counts)

    axes.set_xlabel('RAM (Gb) Being Used')
    axes.set_ylabel('Department')
    axes.set_title('RAM Usage')

    plt.savefig("static/departments_ram.png", bbox_inches='tight')

    return render_template("departments.jinja", departments=all_departments)

def get_department_info():
    """
    Get department information
    """

    all_machines = (
        supabase.table("Machines").select("user_id", "specification_id")
        .neq("state", "DELETED").execute().data
    )
    all_users = supabase.table("Users").select("user_id", "group_id").execute().data
    all_groups = (
        {group["group_id"]: group["department_id"]
         for group in supabase.table("Groups")
         .select("group_id", "department_id")
         .execute().data}
    )
    all_specifications = (
        {spec["specification_id"]: spec
        for spec in supabase.table("Specifications")
        .select("*").execute().data}
    )

    users_in_group = {}
    for user in all_users:
        users_in_group.setdefault(user["group_id"], []).append(user["user_id"])

    machines_by_user = {}
    for machine in all_machines:
        machines_by_user.setdefault(machine["user_id"], []).append(machine["specification_id"])

    group_total_usage = {}
    for group_id, group_users in users_in_group.items():
        group_total_usage[group_id] = {"ram": 0, "cpus": 0, "gpus": 0}
        for user_id in group_users:
            for spec_id in machines_by_user.get(user_id, []):
                spec = all_specifications.get(spec_id)
                if spec:
                    group_total_usage[group_id]["ram"] += spec["ram_gb"]
                    group_total_usage[group_id]["cpus"] += spec["cpus"]
                    group_total_usage[group_id]["gpus"] += spec["gpus"]

    dep_total_usage = {}
    for group_id, dep_id in all_groups.items():
        dep_total_usage.setdefault(dep_id, {"ram": 0, "cpus": 0, "gpus": 0})
        group_usage = group_total_usage.get(group_id)
        if group_usage:
            dep_total_usage[dep_id]["ram"] += group_usage["ram"]
            dep_total_usage[dep_id]["cpus"] += group_usage["cpus"]
            dep_total_usage[dep_id]["gpus"] += group_usage["gpus"]

    return [
        {"department_id": dep_id, **usage}
        for dep_id, usage in dep_total_usage.items()
    ]

if __name__ == "__main__":
    app.run()
