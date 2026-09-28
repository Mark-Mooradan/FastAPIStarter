from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr
from datetime import date
from enum import Enum


class Availability(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    INSPECTION = "inspection"


class CustomerBase(SQLModel):
    username: str = Field(index=True, unique=True)
    password: str


class Customer(CustomerBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    payments: List["Payment"] = Relationship(back_populates="customer")
    listings: List["Listing"] = Relationship(back_populates="owner")
    rentals: List["Rental"] = Relationship(back_populates="renter")

    def list_game(self, game: "Game", condition: str, price: float):
        return Listing(
            gameid=game.gameid,
            ownerid=self.id,
            condition=condition,
            price=price,
            availability=Availability.INSPECTION,
        )

    def rent_game(self, listing: "Listing"):
        listing.availability = Availability.RENTED
        rental = Rental(
            listingId=listing.listingid,
            renterId=self.id,
            rentalDate=date.today(),
        )
        return rental

    def return_game(self, rental: "Rental", amt: float):
        rental.returnDate = date.today()
        payment = Payment(
            RentalId=rental.rentalId,
            customerId=self.id,
            payment_date=date.today(),
            Amount=amt,
        )
        return payment


class GameBase(SQLModel):
    title: str


class Game(GameBase, table=True):
    gameid: Optional[int] = Field(default=None, primary_key=True)
    listings: List["Listing"] = Relationship(back_populates="game")


class ListingBase(SQLModel):
    gameid: int = Field(foreign_key="game.gameid")
    ownerid: int = Field(foreign_key="customer.id")
    condition: str
    availability: Availability = Availability.AVAILABLE
    price: float


class Listing(ListingBase, table=True):
    listingid: Optional[int] = Field(default=None, primary_key=True)

    game: Optional[Game] = Relationship(back_populates="listings")
    owner: Optional[Customer] = Relationship(back_populates="listings")
    rentals: List["Rental"] = Relationship(back_populates="listing")


class RentalBase(SQLModel):
    listingId: int = Field(foreign_key="listing.listingid")
    renterId: int = Field(foreign_key="customer.id")
    rentalDate: date
    returnDate: Optional[date] = None


class Rental(RentalBase, table=True):
    rentalId: Optional[int] = Field(default=None, primary_key=True)

    listing: Optional[Listing] = Relationship(back_populates="rentals")
    renter: Optional[Customer] = Relationship(back_populates="rentals")
    payments: List["Payment"] = Relationship(back_populates="rental")

    def toJSON(self) -> dict:
        return {
            "rentalId": self.rentalId,
            "listingId": self.listingId,
            "renterId": self.renterId,
            "rentalDate": str(self.rentalDate),
            "returnDate": str(self.returnDate) if self.returnDate else None,
        }


class PaymentBase(SQLModel):
    RentalId: int = Field(foreign_key="rental.rentalId")
    customerId: int = Field(foreign_key="customer.id")
    payment_date: date
    Amount: float


class Payment(PaymentBase, table=True):
    paymentId: Optional[int] = Field(default=None, primary_key=True)

    rental: Optional[Rental] = Relationship(back_populates="payments")
    customer: Optional[Customer] = Relationship(back_populates="payments")

    def toJSON(self) -> dict:
        return {
            "paymentId": self.paymentId,
            "RentalId": self.RentalId,
            "customerId": self.customerId,
            "payment_date": str(self.payment_date),
            "Amount": self.Amount,
        }