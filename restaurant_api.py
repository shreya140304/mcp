# restaurant_api.py
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from rapidfuzz import fuzz
from typing import List

app = FastAPI(title="Restaurant Matching API")

# -------------------------------
# LOAD CSV ONCE
# -------------------------------
df = pd.read_csv("zomato.csv")

# Normalize dish_liked column
df["dish_liked"] = df["dish_liked"].fillna("").str.lower()

def parse_dishes(dish_string: str):
    return [d.strip() for d in dish_string.split(",") if d.strip()]

df["dish_list"] = df["dish_liked"].apply(parse_dishes)

# -------------------------------
# REQUEST SCHEMA
# -------------------------------
class RestaurantRequest(BaseModel):
    dishes: List[str]
    top_k: int = 10

# -------------------------------
# SIMILARITY LOGIC
# -------------------------------
def compute_score(restaurant_dishes, recommended_dishes):
    score = 0
    for r in recommended_dishes:
        for d in restaurant_dishes:
            if fuzz.partial_ratio(r, d) >= 80:
                score += 1
                break
    return score

# -------------------------------
# API ENDPOINT
# -------------------------------
@app.post("/restaurants/match")
def match_restaurants(req: RestaurantRequest):
    recommended = [d.lower() for d in req.dishes]

    df["score"] = df["dish_list"].apply(
        lambda dishes: compute_score(dishes, recommended)
    )

    results = (
        df[df["score"] > 0]
        .sort_values("score", ascending=False)
        .head(req.top_k)
    )

    return {
        "restaurants": [
            {
                "name": row["name"],
                "address": row["address"],
                "location": row["location"],
                "cuisines": row["cuisines"],
                "liked_dishes": row["dish_list"],
                "rating": row["rate"],
                "votes": int(row["votes"]) if not pd.isna(row["votes"]) else None,
                "cost_for_two": row["approx_cost(for two people)"],
                "url": row["url"],
                "score": int(row["score"])
            }
            for _, row in results.iterrows()
        ]
    }
