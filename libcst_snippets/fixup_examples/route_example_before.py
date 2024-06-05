from flask import Flask, Blueprint, g


BUY_PERMISSION = "buy"
ADMIN_PERMISSION = "admin"


app = Flask(__name__)


@app.route("/menu")
def menu():
    # No permissions required
    ...


@app.route("/buy", methods=["GET", "POST"])
def buy():
    g.user.require(BUY_PERMISSION)



@app.route("/items/<item_id>")
def item(item_id):
    item = get_item(item_id)
    if item.archived:
        g.user.require(ADMIN_PERMISSION)
    ...



admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.route("/users")
def users():
    g.user.require(ADMIN_PERMISSION)
    ...


def some_misc_function():
    ...
