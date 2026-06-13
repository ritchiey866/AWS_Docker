import re
from typing import Any

from sqlalchemy import MetaData, Table, func, inspect, insert, select, text, update
from sqlalchemy.sql import delete

from app.extensions import db

IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
SYSTEM_TABLES = frozenset({"alembic_version"})

COLUMN_TYPES = {
    "integer": "INTEGER",
    "serial": "SERIAL",
    "text": "TEXT",
    "varchar": "VARCHAR(255)",
    "boolean": "BOOLEAN",
    "timestamp": "TIMESTAMP",
    "numeric": "NUMERIC",
}


class DbAdminError(Exception):
    pass


def validate_identifier(name: str) -> str:
    normalized = name.strip().lower()
    if not IDENTIFIER_RE.match(normalized):
        raise DbAdminError(
            f"Invalid identifier '{name}'. Use lowercase letters, numbers, and underscores."
        )
    return normalized


def list_tables() -> list[dict[str, Any]]:
    inspector = inspect(db.engine)
    tables: list[dict[str, Any]] = []

    for name in sorted(inspector.get_table_names()):
        if name.startswith("pg_"):
            continue

        row_count = db.session.execute(
            text(f'SELECT COUNT(*) FROM "{name}"')
        ).scalar_one()
        pk_columns = inspector.get_pk_constraint(name).get("constrained_columns") or []

        tables.append(
            {
                "name": name,
                "row_count": row_count,
                "primary_key": pk_columns,
                "is_system": name in SYSTEM_TABLES,
            }
        )

    return tables


def get_table_columns(table_name: str) -> list[dict[str, Any]]:
    name = validate_identifier(table_name)
    inspector = inspect(db.engine)
    if name not in inspector.get_table_names():
        raise DbAdminError(f"Table '{name}' does not exist.")

    pk_columns = set(inspector.get_pk_constraint(name).get("constrained_columns") or [])
    columns = []

    for column in inspector.get_columns(name):
        columns.append(
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "primary_key": column["name"] in pk_columns,
                "default": column.get("default"),
            }
        )

    return columns


def get_primary_key_columns(table_name: str) -> list[str]:
    inspector = inspect(db.engine)
    name = validate_identifier(table_name)
    return inspector.get_pk_constraint(name).get("constrained_columns") or []


def reflect_table(table_name: str) -> Table:
    name = validate_identifier(table_name)
    metadata = MetaData()
    return Table(name, metadata, autoload_with=db.engine)


def create_table(table_name: str, columns: list[dict[str, Any]]) -> None:
    name = validate_identifier(table_name)

    if not columns:
        raise DbAdminError("At least one column is required.")

    inspector = inspect(db.engine)
    if name in inspector.get_table_names():
        raise DbAdminError(f"Table '{name}' already exists.")

    definitions: list[str] = []
    has_primary_key = False

    for column in columns:
        col_name = validate_identifier(column["name"])
        col_type = column.get("type", "text")
        if col_type not in COLUMN_TYPES:
            raise DbAdminError(f"Unsupported column type '{col_type}'.")

        parts = [f'"{col_name}" {COLUMN_TYPES[col_type]}']

        if column.get("primary_key"):
            if col_type == "serial":
                parts.append("PRIMARY KEY")
            else:
                parts.append("PRIMARY KEY")
            has_primary_key = True
        elif not column.get("nullable", True):
            parts.append("NOT NULL")

        definitions.append(" ".join(parts))

    if not has_primary_key:
        raise DbAdminError("At least one primary key column is required.")

    sql = f'CREATE TABLE "{name}" ({", ".join(definitions)})'
    db.session.execute(text(sql))
    db.session.commit()


def drop_table(table_name: str) -> None:
    name = validate_identifier(table_name)
    if name in SYSTEM_TABLES:
        raise DbAdminError(f"Table '{name}' is protected and cannot be dropped.")

    db.session.execute(text(f'DROP TABLE "{name}" CASCADE'))
    db.session.commit()


def fetch_rows(
    table_name: str,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    table = reflect_table(table_name)
    page = max(page, 1)
    offset = (page - 1) * per_page

    rows = db.session.execute(select(table).limit(per_page).offset(offset)).mappings().all()
    total = db.session.execute(select(func.count()).select_from(table)).scalar_one()
    return [dict(row) for row in rows], total


def _coerce_value(column_meta: dict[str, Any], raw_value: str | None) -> Any:
    if raw_value is None or raw_value == "":
        if column_meta["primary_key"] and "serial" in column_meta["type"].lower():
            return None
        return None if column_meta["nullable"] else ""

    type_name = column_meta["type"].lower()

    if "boolean" in type_name:
        return raw_value.lower() in {"1", "true", "yes", "on"}
    if "int" in type_name:
        return int(raw_value)
    if "numeric" in type_name or "float" in type_name:
        return float(raw_value)

    return raw_value


def _column_meta_map(table_name: str) -> dict[str, dict[str, Any]]:
    return {column["name"]: column for column in get_table_columns(table_name)}


def _filter_payload(table_name: str, payload: dict[str, str]) -> dict[str, Any]:
    columns = _column_meta_map(table_name)
    values: dict[str, Any] = {}

    for name, meta in columns.items():
        if meta["primary_key"] and "serial" in meta["type"].lower() and name not in payload:
            continue
        if name not in payload:
            continue
        values[name] = _coerce_value(meta, payload.get(name))

    return values


def insert_row(table_name: str, payload: dict[str, str]) -> None:
    table = reflect_table(table_name)
    values = _filter_payload(table_name, payload)
    db.session.execute(insert(table).values(**values))
    db.session.commit()


def get_row(table_name: str, pk_values: dict[str, str]) -> dict[str, Any] | None:
    table = reflect_table(table_name)
    pk_columns = get_primary_key_columns(table_name)
    if not pk_columns:
        raise DbAdminError(f"Table '{table_name}' has no primary key.")

    stmt = select(table)
    for column in pk_columns:
        if column not in pk_values:
            raise DbAdminError(f"Missing primary key value for '{column}'.")
        stmt = stmt.where(table.c[column] == pk_values[column])

    row = db.session.execute(stmt).mappings().first()
    return dict(row) if row else None


def update_row(
    table_name: str,
    pk_values: dict[str, str],
    payload: dict[str, str],
) -> None:
    table = reflect_table(table_name)
    pk_columns = get_primary_key_columns(table_name)
    values = _filter_payload(table_name, payload)

    for column in pk_columns:
        values.pop(column, None)

    stmt = update(table)
    for column in pk_columns:
        stmt = stmt.where(table.c[column] == pk_values[column])

    db.session.execute(stmt.values(**values))
    db.session.commit()


def delete_row(table_name: str, pk_values: dict[str, str]) -> None:
    table = reflect_table(table_name)
    pk_columns = get_primary_key_columns(table_name)

    stmt = delete(table)
    for column in pk_columns:
        stmt = stmt.where(table.c[column] == pk_values[column])

    db.session.execute(stmt)
    db.session.commit()


def pk_values_from_form(table_name: str, form_data) -> dict[str, str]:
    pk_columns = get_primary_key_columns(table_name)
    values = {column: form_data.get(column, "") for column in pk_columns}
    if any(value == "" for value in values.values()):
        raise DbAdminError("Missing primary key values.")
    return values
