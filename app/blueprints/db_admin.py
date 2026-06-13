from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.db_admin import (
    COLUMN_TYPES,
    DbAdminError,
    create_table,
    delete_row,
    drop_table,
    fetch_rows,
    get_primary_key_columns,
    get_row,
    get_table_columns,
    insert_row,
    list_tables,
    pk_values_from_form,
    update_row,
    validate_identifier,
)

db_admin_bp = Blueprint("db_admin", __name__, url_prefix="/db")


@db_admin_bp.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))


@db_admin_bp.route("/")
def list_all_tables():
    tables = list_tables()
    return render_template("db/tables.html", tables=tables)


@db_admin_bp.route("/tables/create", methods=["GET", "POST"])
def create_table_view():
    if request.method == "POST":
        table_name = request.form.get("table_name", "").strip()
        col_names = request.form.getlist("col_name")
        col_types = request.form.getlist("col_type")
        col_pk = set(request.form.getlist("col_pk"))
        col_nullable = set(request.form.getlist("col_nullable"))

        columns = []
        for index, name in enumerate(col_names):
            name = name.strip()
            if not name:
                continue
            columns.append(
                {
                    "name": name,
                    "type": col_types[index] if index < len(col_types) else "text",
                    "primary_key": name in col_pk,
                    "nullable": name in col_nullable,
                }
            )

        try:
            create_table(table_name, columns)
            flash(f"Table '{validate_identifier(table_name)}' created.", "success")
            return redirect(url_for("db_admin.table_detail", table_name=table_name))
        except (DbAdminError, ValueError) as exc:
            flash(str(exc), "error")

    return render_template("db/create_table.html", column_types=COLUMN_TYPES)


@db_admin_bp.route("/tables/<table_name>/")
def table_detail(table_name):
    page = request.args.get("page", 1, type=int)
    try:
        columns = get_table_columns(table_name)
        rows, total = fetch_rows(table_name, page=page)
        pk_columns = get_primary_key_columns(table_name)
    except DbAdminError as exc:
        flash(str(exc), "error")
        return redirect(url_for("db_admin.list_all_tables"))

    per_page = 50
    total_pages = max((total + per_page - 1) // per_page, 1)

    return render_template(
        "db/table_detail.html",
        table_name=table_name,
        columns=columns,
        rows=rows,
        pk_columns=pk_columns,
        page=page,
        total=total,
        total_pages=total_pages,
    )


@db_admin_bp.route("/tables/<table_name>/rows/new", methods=["GET", "POST"])
def create_row(table_name):
    try:
        columns = get_table_columns(table_name)
    except DbAdminError as exc:
        flash(str(exc), "error")
        return redirect(url_for("db_admin.list_all_tables"))

    if request.method == "POST":
        try:
            insert_row(table_name, request.form)
            flash("Row created.", "success")
            return redirect(url_for("db_admin.table_detail", table_name=table_name))
        except (DbAdminError, ValueError) as exc:
            flash(str(exc), "error")

    return render_template(
        "db/row_form.html",
        table_name=table_name,
        columns=columns,
        row={},
        action="create",
    )


@db_admin_bp.route("/tables/<table_name>/rows/edit", methods=["GET", "POST"])
def edit_row(table_name):
    try:
        columns = get_table_columns(table_name)
        pk_values = pk_values_from_form(table_name, request.values)
        row = get_row(table_name, pk_values)
        if row is None:
            flash("Row not found.", "error")
            return redirect(url_for("db_admin.table_detail", table_name=table_name))
    except DbAdminError as exc:
        flash(str(exc), "error")
        return redirect(url_for("db_admin.table_detail", table_name=table_name))

    if request.method == "POST":
        try:
            if validate_identifier(table_name) == "users":
                password = request.form.get("password_hash", "")
                username = request.form.get("username", "").strip()
                if not password and username == row.get("username", ""):
                    return redirect(url_for("db_admin.table_detail", table_name=table_name))

            updated = update_row(table_name, pk_values, request.form)
            if updated:
                flash("Row updated.", "success")
            return redirect(url_for("db_admin.table_detail", table_name=table_name))
        except (DbAdminError, ValueError) as exc:
            flash(str(exc), "error")

    return render_template(
        "db/row_form.html",
        table_name=table_name,
        columns=columns,
        row=row,
        action="edit",
        pk_values=pk_values,
    )


@db_admin_bp.route("/tables/<table_name>/rows/delete", methods=["POST"])
def delete_row_view(table_name):
    try:
        pk_values = pk_values_from_form(table_name, request.form)
        delete_row(table_name, pk_values)
        flash("Row deleted.", "success")
    except DbAdminError as exc:
        flash(str(exc), "error")

    return redirect(url_for("db_admin.table_detail", table_name=table_name))


@db_admin_bp.route("/tables/<table_name>/drop", methods=["POST"])
def drop_table_view(table_name):
    try:
        drop_table(table_name)
        flash(f"Table '{table_name}' dropped.", "success")
    except DbAdminError as exc:
        flash(str(exc), "error")

    return redirect(url_for("db_admin.list_all_tables"))
