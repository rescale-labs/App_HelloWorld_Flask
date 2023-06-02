import os
import subprocess

from flask import Blueprint, Flask, jsonify, render_template, url_for, request

RESCALE_CLUSTER_ID = os.getenv("RESCALE_CLUSTER_ID")
PREFIX = (
    "/local/"
    if RESCALE_CLUSTER_ID == None
    else f"/notebooks/{os.getenv('RESCALE_CLUSTER_ID')}/"
)

app = Flask(__name__)

rescale_bp = Blueprint(
    "rescale_app",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path=f"assets",
    url_prefix=PREFIX,
)


def get_headers(req, cutoff=200):
    return {
        k: str(v) if len(str(v)) <= cutoff else str(v)[:cutoff] + "..."
        for k, v in dict(
            filter(lambda p: True if "w" not in p[0] and len(str(p[1])) > 0 else False, req.environ.items())
        ).items()
    }


def get_top(count):
    return subprocess.run(
        f"ps auxc | grep -v '%CPU' | sort -r -nk 3 | awk '{{print $3,\"\t\",$11}}' | head -{count}",
        shell=True,
        stdout=subprocess.PIPE,
    ).stdout.decode()


@rescale_bp.route("/style")
def style():
    return render_template(
        "style.html",
        headers=get_headers(request),
        top_20=get_top(20).replace("\n", "<br/>"),
        static_path=rescale_bp.static_url_path,
    )


@rescale_bp.route("/script")
def scripted():
    return render_template("script.html", base_url=rescale_bp.url_prefix)


@rescale_bp.route("/form", methods=["GET", "POST"])
def formed():
    count = 20
    if request.method == "POST":
        count = request.form.get("count", default=20)

    return render_template("form.html", top=get_top(count), count=count)


@rescale_bp.route("/api/top")
def api_top():
    top = get_top(request.args.get("count", default=20))
    lines = []
    for l in top.split("\n"):
        if len(l.strip()) > 0:
            cpu, proc = l.split("\t")
            lines.append({"cpu": float(cpu), "proc": proc.strip()})

    return jsonify(top=lines)


@rescale_bp.route("/")
def hello():
    return "Blueprint Hello World!"


@rescale_bp.route("/.rescale-app")
def metadata():
    return {
        "name": "Rescale App : Hello Worls",
        "description": "A simple example of a Rescale App",
        "helpUrl": "https://github.com/rescale-labs/App_HelloWorld_Flask",
        "icon": f"{PREFIX}{rescale_bp.static_url_path}/rescale_logo.svg",
        "supportEmail": "support@rescale.com",
        "webappUrl": PREFIX,
        "isActive": True,
    }


@app.route("/", defaults={"path": ""})
@rescale_bp.route("/echo/<path:path>")
def catch_all(path):
    return render_template(
        "index.html", headers=get_headers(request), top_20=get_top(20)
    )


@app.route("/hello")
def hello():
    return "Hello World!"


app.register_blueprint(rescale_bp)


if __name__ == "__main__":
    app.run()
