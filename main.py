from fastapi import FastAPI, Query
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # Loads environment variables from .env if present

app = FastAPI()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database()  # Automatically picks from URI
collection = db["recipes"]  # Assuming your collection is named 'recipes'

@app.get("/")
def read_root():
    return {"message": "Recipe API (MongoDB) is running"}

@app.get("/recipes")
def get_all_recipes(limit: int = 100):
    cursor = collection.find({}, {"_id": 0}).limit(limit)
    return list(cursor)

@app.get("/search")
def search_recipes(query: str = Query(...), limit: int = 20):
    cursor = collection.find({"NER": {"$regex": query, "$options": "i"}}, {"_id": 0}).limit(limit)
    return list(cursor)

@app.get("/recipes/{index}")
def get_recipe_by_index(index: int):
    doc = collection.find().skip(index).limit(1)
    result = list(doc)
    return result[0] if result else {"error": "Recipe not found"}
