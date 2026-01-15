from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import pandas as pd
import uuid
import numpy as np
import os

# from google.colab import userdata
from dotenv import load_dotenv

load_dotenv()

_q_host = os.getenv("QDRANT_CLIENT")
_q_key = os.getenv("QDRANT_API_KEY")
print("QDRANT_CLIENT:", _q_host)
print("QDRANT_API_KEY (masked):", (_q_key[:4] + "..." + _q_key[-4:]) if _q_key else None)

class FoodRecommendationSystem:
    def __init__(self, model_name='all-MiniLM-L6-v2', qdrant_host="localhost", qdrant_port=6333):
        """Initialize the food recommendation system"""
        self.model = SentenceTransformer(model_name)
        self.client = QdrantClient(url=os.getenv("QDRANT_CLIENT"), api_key=os.getenv("QDRANT_API_KEY"))
        self.collection_name = "indian_food_db"


    def search_foods(self, query, limit=5):
        """Search for foods based on query and optional nutrition filters"""

        # Generate embedding for the query
        query_embedding = self.model.encode([query]).tolist()[0]


        # Perform search
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            with_payload=True
        )

        return results.points


    def search_foods_with_payload(self, query, filters=None, limit=5):

      query_embedding = self.model.encode([query]).tolist()[0]

      filter_conditions = []
      if filters:
          for nutrient, (min_val, max_val) in filters.items():
              filter_conditions.append(
                  models.FieldCondition(
                      key=f"nutrition.{nutrient}",
                      range=models.Range(
                        gt=None,
                        gte=min_val,
                        lt=None,
                        lte=max_val,
                     ),
                  )
              )

      query_filter = None
      if filter_conditions:
          query_filter = models.Filter(must=filter_conditions)

      results = self.client.query_points(
          collection_name=self.collection_name,
          query=query_embedding,
          limit=limit,
          query_filter=query_filter,
          with_payload=True
      )

      return results.points

    def recommend_by_ingredients(self, ingredients_list, limit=5):
        """Find foods with similar ingredients"""
        ingredients_query = f"dish with {', '.join(ingredients_list)}"
        return self.search_foods(ingredients_query, limit=limit)


def print_recommendations(results, title):
    """Utility function to print recommendation results"""
    print(f"\n{title}:")
    print("-" * 50)
    for i, result in enumerate(results, 1):
        # print(result)
        payload = result.payload
        print(f"{i}. {payload['food_name']} (Score: {result.score:.3f})")
        print(f"   Ingredients: {', '.join(payload['ingredients'])}")
        nutrition = payload['nutrition']
        print(f"   Nutrition: {nutrition['energy_kcal']:.1f} kcal, "
              f"{nutrition['protein_g']:.1f}g protein, "
              f"{nutrition['carb_g']:.1f}g carbs, "
              f"{nutrition['fat_g']:.1f}g fat")
        print()

if __name__ == "__main__":

    food_system = FoodRecommendationSystem()


    # Example 1: Search for high protein, low calorie foods
    high_protein_results = food_system.search_foods(
        "high protein healthy vegan food",
        limit=5
    )
    print_recommendations(high_protein_results, "High Protein, Low Calorie Foods")

    # Example 2: Find foods similar to specific ingredients
    similar_to_chicken_rice = food_system.recommend_by_ingredients(['chicken', 'rice', 'vegetables'])
    print_recommendations(similar_to_chicken_rice, "Similar to Chicken & Rice Dishes")

    # Example 3: Find foods similar to specific ingredients
    similar_to_chicken_rice = food_system.recommend_by_ingredients(['Paneer', 'rice', 'vegetables'])
    print_recommendations(similar_to_chicken_rice, "Similar to Paneer & Rice Dishes")

    healty_vegetarian = food_system.search_foods("Healthy Vegetarian with Good Fiber", limit=5)
    print_recommendations(healty_vegetarian, "Healthy Vegetarian with Good Fiber")


    print("\n\n\nFiltering using Payload with Range condition")

    high_protein_results = food_system.search_foods_with_payload(
        "high protein",
        filters={
            'protein_g': (12, 20)
        },
        limit=10
    )
    print_recommendations(high_protein_results, "High Protein Foods")

    high_carb_results = food_system.search_foods_with_payload(
        "high carb",
        filters={
            'carb_g': (60, 64)
        },
        limit=10
    )
    print_recommendations(high_carb_results, "High Carb Foods")


    high_prot_and_carb_results = food_system.search_foods_with_payload(
        "high carb and high protein",
        filters={
            'carb_g': (30, None),
            'protein_g': (10, None),
        },
        limit=10
    )
    print_recommendations(high_prot_and_carb_results, "High Carb and Protein Foods")


    high_prot_and_carb_results = food_system.search_foods_with_payload(
        "high carb and high protein",
        limit=10
    )
    print_recommendations(high_prot_and_carb_results, "High Carb and Protein Foods without payload filtering")
def xyz(query: str, filters: dict | None = None, limit: int = 5):
    """
    Main entry point for frontend.
    query   : user natural language input
    filters : nutrition filters (protein_g, carb_g, fat_g, etc.)
    """

    food_system = FoodRecommendationSystem()

    # Decide which search to run
    if filters:
        results = food_system.search_foods_with_payload(
            query=query,
            filters=filters,
            limit=limit
        )
    else:
        results = food_system.search_foods(
            query=query,
            limit=limit
        )

    # Convert Qdrant results → structured JSON
    output = []
    for result in results:
        payload = result.payload
        nutrition = payload["nutrition"]

        output.append({
            "food_name": payload["food_name"],
            "score": round(result.score, 3),
            "ingredients": payload["ingredients"],
            "nutrition": {
                "energy_kcal": round(nutrition["energy_kcal"], 1),
                "protein_g": round(nutrition["protein_g"], 1),
                "carb_g": round(nutrition["carb_g"], 1),
                "fat_g": round(nutrition["fat_g"], 1),
            }
        })

    return {
        "query": query,
        "applied_filters": filters,
        "results": output
    }
