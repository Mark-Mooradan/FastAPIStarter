from app.database import get_cli_session
from app.models import Customer, Game

with get_cli_session() as session:
    if not session.exec(__import__("sqlmodel").select(Customer)).first():
        session.add(Customer(username="alice", password="pw"))
        session.add(Game(title="Elden Ring"))
        session.add(Game(title="Zelda: Tears of the Kingdom"))
        session.commit()
        print("Seeded alice/pw and two games.")
    else:
        print("Already seeded.")