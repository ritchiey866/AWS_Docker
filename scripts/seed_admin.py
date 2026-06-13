from werkzeug.security import generate_password_hash

from app.extensions import db
from app.factory import create_app
from app.models.user import User


def seed_admin() -> None:
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username="admin").first() is None:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("password"),
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user.")
        else:
            print("Admin user already exists.")


if __name__ == "__main__":
    seed_admin()
