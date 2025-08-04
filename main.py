import os
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from bson.objectid import ObjectId

app = FastAPI(
    title="FridgeChef Recipe API",
    description="Search and fetch recipes from MongoDB",
    version="1.0.0",
)

# 1. Load MongoDB URI from env
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Please set the MONGO_URI environment variable")

# 2. Connect
client = MongoClient(MONGO_URI)
db = client["recipes_list"]          # <-- your database name
collection = db["recipes_data"]      # <-- your collection name

def serialize_doc(doc: dict) -> dict:
    """
    Convert MongoDB's ObjectId to string so JSON encoding works.
    """
    doc["_id"] = str(doc["_id"])
    return doc

@app.get("/")
def root():
    return {"message": "Welcome to FridgeChef Recipe API"}

@app.get("/search", summary="Search recipes by keyword")
def search_recipes(
    query: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(5, ge=1, le=100, description="Max number of results"),
):
    # Case‐insensitive regex match on multiple fields
    regex = {"$regex": query, "$options": "i"}
    cursor = collection.find(
        {
            "$or": [
                {"NER": regex},
                {"ingredients": regex},
                {"directions": regex},
                {"title": regex},
            ]
        }
    ).limit(limit)

    results = [serialize_doc(doc) for doc in cursor]
    return results

@app.get("/recipes/{number}", summary="Get a recipe by its number")
def get_recipe(number: int):
    doc = collection.find_one({"number": number})
    if not doc:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return serialize_doc(doc)
