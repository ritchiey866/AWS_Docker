from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models.item import Item

items_bp = Blueprint("items", __name__, url_prefix="/items")


@items_bp.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))


@items_bp.route("/")
def list_items():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template("items/list.html", items=items)


@items_bp.route("/new", methods=["GET", "POST"])
def create_item():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Name is required.", "error")
            return render_template("items/form.html", item=None)

        item = Item(name=name, description=description or None)
        db.session.add(item)
        db.session.commit()
        flash("Item created.", "success")
        return redirect(url_for("items.list_items"))

    return render_template("items/form.html", item=None)


@items_bp.route("/<int:item_id>")
def view_item(item_id):
    item = db.get_or_404(Item, item_id)
    return render_template("items/detail.html", item=item)


@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    item = db.get_or_404(Item, item_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Name is required.", "error")
            return render_template("items/form.html", item=item)

        item.name = name
        item.description = description or None
        db.session.commit()
        flash("Item updated.", "success")
        return redirect(url_for("items.view_item", item_id=item.id))

    return render_template("items/form.html", item=item)


@items_bp.route("/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    item = db.get_or_404(Item, item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("items.list_items"))
