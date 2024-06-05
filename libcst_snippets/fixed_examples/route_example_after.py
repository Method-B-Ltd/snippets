from flask import Flask, Blueprint, g


BUY_PERMISSION = "buy"
ADMIN_PERMISSION = "admin"


app = Flask(__name__)


@app.route("/menu")
def menu():
    # No permissions required
    ...


@app.route("/buy", methods=["GET", "POST"], permission=BUY_PERMISSION)
def buy():
    pass



@app.route("/items/<item_id>")
def item(item_id):
    item = get_item(item_id)
    if item.archived:
        g.user.require(ADMIN_PERMISSION)
    ...



admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.route("/users", permission=ADMIN_PERMISSION)
def users():
    ...


def some_misc_function():
    ...
