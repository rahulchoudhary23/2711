from flask import Blueprint
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
def admin_home():
    if current_user.role != "admin":
        return "Unauthorized", 403

    return "Admin dashboard live!"

