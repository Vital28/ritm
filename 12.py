from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()

# Create the database engine
engine = create_engine("sqlite:///example.db")

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our models
Base = declarative_base()


# Define a model for our table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    identification_number = Column(String)
    status = Column(Boolean, default=False)
    last_log = Column(DateTime)


# Create the database tables
Base.metadata.create_all(bind=engine)


# Dependency to get a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Define your endpoints here using FastAPI decorators


@app.get("/table", response_class=HTMLResponse)
async def get_table():
    # Mock data for example purposes
    data = [
        {"First name": "John", "Last name": "Doe", "Identification number": "123", "Status": "SUCCESS",
         "Last log": "2022-02-24 15:30:00"},
        {"First name": "Jane", "Last name": "Doe", "Identification number": "456", "Status": "PENDING",
         "Last log": "2022-02-23 10:15:00"},
        {"First name": "Bob", "Last name": "Smith", "Identification number": "789", "Status": "IN_PROGRESS",
         "Last log": "2022-02-22 08:00:00"},
        {"First name": "Alice", "Last name": "Jones", "Identification number": "234", "Status": "WAITING_FOR_CODE",
         "Last log": "2022-02-21 13:45:00"},
        {"First name": "Sam", "Last name": "Brown", "Identification number": "567", "Status": "IN_PROGRESS",
         "Last log": "2022-02-20 18:00:00"},
        {"First name": "Tom", "Last name": "Green", "Identification number": "890", "Status": "FAIL",
         "Last log": "2022-02-19 09:30:00"},
        {"First name": "Sara", "Last name": "Lee", "Identification number": "123", "Status": "IN_PROGRESS",
         "Last log": "2022-02-18 11:00:00"}
    ]

    # Generate the HTML table
    table_html = "<table>"
    for row in data:
        # Set the background color of the cell based on the status column
        if row["Status"] == "SUCCESS":
            row_html = "<tr style='background-color: green;'>"
        elif row["Status"] == "PENDING":
            row_html = "<tr style='background-color: yellow;'>"
        elif row["Status"] == "IN_PROGRESS":
            row_html = "<tr style='background-color: blue;'>"
        elif row["Status"] == "WAITING_FOR_CODE":
            row_html = "<tr style='background-color: orange;'>"
        elif row["Status"] == "FAIL":
            row_html = "<tr style='background-color: red;'>"
        else:
            row_html = "<tr>"

        # Add the row data to the HTML table
        row_html += "<td>" + row["First name"] + "</td>"
        row_html += "<td>" + row["Last name"] + "</td>"
        row_html += "<td>" + row["Identification number"] + "</td>"
        row_html += "<td>" + row["Status"] + "</td>"
        row_html += "<td>" + row["Last log"] + "</td>"
        row_html += "</tr>"

        table_html += row_html

    table_html += "</table>"

    return table_html


class StatusEnum(str, Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_CODE = "WAITING_FOR_CODE"


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    id_number = Column(String, nullable=False, unique=True)
    status = Column(StatusEnum, nullable=False, default=StatusEnum.PENDING)
    last_log = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


@app.post("/people", status_code=status.HTTP_201_CREATED)
async def create_person(first_name: str, last_name: str, id_number: str, db=Depends(get_db)):
    # Check if a person with the same ID number already exists
    person = db.query(Person).filter_by(id_number=id_number).first()
    if person:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Person with this ID number already exists")

    # Create the new person
    new_person = Person(first_name=first_name, last_name=last_name, id_number=id_number)
    db.add(new_person)
    db.commit()
    db.refresh(new_person)

    return new_person


# Define an endpoint to get a list of people, with filters and search functionality
@app.get("/people", response_model=List[Person])
async def get_people(status: Optional[StatusEnum] = None, search: Optional[str] = None, db=Depends(get_db)):
    query = db.query(Person)

    # Filter by status, if specified
    if status:
        query = query.filter_by(status=status)

    # Search by first or last name, if specified
    if search:
        query = query.filter(
            (Person.first_name.ilike(f"%{search}%")) |
            (Person.last_name.ilike(f"%{search}%"))
        )

    # Colorize rows based on status
    query = query.order_by(
        text(
            "CASE "
            f"WHEN status = '{StatusEnum.FAIL}' THEN '{status.HTTP_400_BAD_REQUEST}' "
            f"WHEN status = '{StatusEnum.SUCCESS}' THEN '{status.HTTP_200_OK}' "
            f"WHEN status = '{StatusEnum.PENDING}' THEN '{status.HTTP_202_ACCEPTED}' "
            f"WHEN status = '{StatusEnum.IN_PROGRESS}' THEN '{status.HTTP_100_CONTINUE}' "))
