from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
import csv

# Define the SQLModel table
class Dish(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dish_name: str
    ingredients: str
    recipe: str

# Database setup
sqlite_file_name = "dishes.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

# Create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Load CSV data into database
def import_csv_to_db(csv_filename: str):
    with open(csv_filename, newline='', encoding='utf-8') as csvfile, Session(engine) as session:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dish = Dish(
                dish_name=row['dish_name'],
                ingredients=row['ingredients'],
                recipe=row['recipe']
            )
            session.add(dish)
        session.commit()

# FastAPI app setup
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    import_csv_to_db("dishes.csv")  # Import/update DB on start

@app.get("/dishes/", response_model=list[Dish])
def get_dishes():
    with Session(engine) as session:
        dishes = session.exec(select(Dish)).all()
        return dishes

from fastapi import Query

@app.get("/dishes/search")
def search_dish(name: str = Query(...)):
    with Session(engine) as session:
        dish = session.exec(select(Dish).where(Dish.dish_name == name)).first()
        if not dish:
            raise HTTPException(status_code=404, detail="Dish not found")
        return dish

@app.get("/dishes/{dish_id}", response_model=Dish)
def get_dish(dish_id: int):
    with Session(engine) as session:
        dish = session.get(Dish, dish_id)
        if not dish:
            raise HTTPException(status_code=404, detail="Dish not found")
        return dish
@app.get("/")
def root():
    return {"message": "API is running. See /docs for endpoints."}

