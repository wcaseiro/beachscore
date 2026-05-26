from flask import Blueprint, render_template


views_bp = Blueprint("views", __name__)


@views_bp.get("/")
def placar():
    return render_template("placar.html")


@views_bp.get("/control")
def control():
    return render_template("control.html")


@views_bp.get("/admin")
def admin():
    return render_template("admin.html")
