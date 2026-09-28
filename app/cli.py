from datetime import date, timedelta
from sqlmodel import select

from app.database import get_cli_session
from app.models import (
    Customer, Game, Listing, Rental, Payment, Availability,
)

LATE_FEE_PER_DAY = 5.00
RENTAL_PERIOD_DAYS = 7


def login(session) -> Customer | None:
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    customer = session.exec(
        select(Customer).where(Customer.username == username)
    ).first()
    if not customer or customer.password != password:
        print("[X] Invalid credentials.\n")
        return None
    print(f"[OK] Logged in as {customer.username}\n")
    return customer


def view_game_catalogue():
    with get_cli_session() as session:
        games = session.exec(select(Game)).all()
        if not games:
            print("\nNo games in the catalogue yet.\n")
            return

        print("\n" + "=" * 60)
        print("                  GAME CATALOGUE")
        print("=" * 60)
        for game in games:
            print(f"\n  {game.title}  (id={game.gameid})")
            print("-" * 60)
            if not game.listings:
                print("   (no listings)")
                continue
            for l in game.listings:
                marker = "[OK]" if l.availability == Availability.AVAILABLE else "[X]"
                print(
                    f"   {marker} Listing #{l.listingid} | "
                    f"Price: ${l.price:.2f} | "
                    f"Condition: {l.condition} | "
                    f"Status: {l.availability.value}"
                )
        print("\n" + "=" * 60 + "\n")


def list_game(customer: Customer):
    with get_cli_session() as session:
        customer = session.get(Customer, customer.id)

        title = input("Game title to list: ").strip()
        if not title:
            print("[X] Title cannot be empty.\n")
            return

        game = session.exec(select(Game).where(Game.title == title)).first()
        if not game:
            print(f"Game '{title}' not in catalogue. Adding it as a new game.")
            game = Game(title=title)
            session.add(game)
            session.commit()
            session.refresh(game)

        condition = input("Condition (Like New / Good / Fair): ").strip()
        if not condition:
            print("[X] Condition cannot be empty.\n")
            return

        try:
            price = float(input("Rental price: ").strip())
            if price < 0:
                raise ValueError
        except ValueError:
            print("[X] Invalid price. Must be a non-negative number.\n")
            return

        listing = Listing(
            gameid=game.gameid,
            ownerid=customer.id,
            condition=condition,
            price=price,
            availability=Availability.INSPECTION,
        )
        session.add(listing)
        session.commit()
        session.refresh(listing)

        print(
            f"[OK] Listed '{game.title}' as Listing #{listing.listingid} "
            f"(pending staff inspection).\n"
        )


def rent_game(customer: Customer):
    with get_cli_session() as session:
        customer = session.get(Customer, customer.id)

        try:
            listing_id = int(input("Enter Listing ID to rent: ").strip())
        except ValueError:
            print("[X] Invalid ID.\n")
            return

        listing = session.get(Listing, listing_id)
        if not listing:
            print("[X] Listing not found.\n")
            return

        if listing.availability != Availability.AVAILABLE:
            print(f"[X] Listing is not available ({listing.availability.value}).\n")
            return

        if listing.ownerid == customer.id:
            print("[X] You can't rent your own listing.\n")
            return

        listing.availability = Availability.RENTED

        rental = Rental(
            listingId=listing.listingid,
            renterId=customer.id,
            rentalDate=date.today(),
            returnDate=date.today() + timedelta(days=RENTAL_PERIOD_DAYS),
        )
        session.add(rental)
        session.add(listing)
        session.commit()
        session.refresh(rental)

        print(
            f"[OK] Rented Listing #{listing.listingid} "
            f"(Rental #{rental.rentalId}). Due back by {rental.returnDate}.\n"
        )


def return_game(customer: Customer):
    with get_cli_session() as session:
        customer = session.get(Customer, customer.id)

        try:
            rental_id = int(input("Enter Rental ID to return: ").strip())
        except ValueError:
            print("[X] Invalid ID.\n")
            return

        rental = session.get(Rental, rental_id)
        if not rental:
            print("[X] Rental not found.\n")
            return

        if rental.renterId != customer.id:
            print("[X] This rental isn't yours.\n")
            return

        listing = session.get(Listing, rental.listingId)
        if not listing:
            print("[X] Listing not found for this rental.\n")
            return

        today = date.today()
        late_days = 0
        if rental.returnDate and today > rental.returnDate:
            late_days = (today - rental.returnDate).days
        late_fee = late_days * LATE_FEE_PER_DAY

        rental_fee = listing.price
        total_due = rental_fee + late_fee

        print(f"\nRental #{rental.rentalId}")
        print(f"  Game       : {listing.game.title if listing.game else '(unknown)'}")
        print(f"  Rental fee : ${rental_fee:.2f}")
        print(f"  Due date   : {rental.returnDate}")
        print(f"  Returned   : {today}")
        print(f"  Late days  : {late_days}")
        print(f"  Late fee   : ${late_fee:.2f}  (${LATE_FEE_PER_DAY:.2f}/day)")
        print(f"  TOTAL DUE  : ${total_due:.2f}\n")

        payment = Payment(
            RentalId=rental.rentalId,
            customerId=customer.id,
            payment_date=today,
            Amount=total_due,
        )
        session.add(payment)

        listing.availability = Availability.AVAILABLE
        session.add(listing)

        session.commit()
        session.refresh(payment)

        print(
            f"[OK] Returned. Payment #{payment.paymentId} "
            f"of ${total_due:.2f} recorded.\n"
        )


def customer_menu(customer: Customer):
    while True:
        print(f"=== Customer Menu ({customer.username}) ===")
        print("1. View Game Catalogue")
        print("2. List a Game for Rent")
        print("3. Rent a Game")
        print("4. Return a Game with Payment")
        print("0. Logout")
        choice = input("Choose: ").strip()

        if choice == "1":
            view_game_catalogue()
        elif choice == "2":
            list_game(customer)
        elif choice == "3":
            rent_game(customer)
        elif choice == "4":
            return_game(customer)
        elif choice == "0":
            print("Logged out.\n")
            return
        else:
            print("Invalid choice.\n")


def main():
    while True:
        print("=== Game Rental CLI ===")
        print("1. View Game Catalogue")
        print("2. Login as Customer")
        print("0. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            view_game_catalogue()
        elif choice == "2":
            with get_cli_session() as session:
                customer = login(session)
            if customer:
                customer_menu(customer)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()