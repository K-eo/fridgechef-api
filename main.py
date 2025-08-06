import os
from fastapi import FastAPI, HTTPException, Query, Body
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime

app = FastAPI(
    title="FridgeChef Recipe API",
    description="Search and fetch recipes from MongoDB",
    version="1.0.0",
)

# MongoDB URI from environment
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Please set the MONGO_URI environment variable")

# Connect to client
client = MongoClient(MONGO_URI)

# Databases and collections
recipes_db = client["recipes_list"]
recipes_collection = recipes_db["recipes_data"]

fridgechef_db = client["fridgechef"]
reviews_collection = fridgechef_db["reviews"]
messages_collection = fridgechef_db["important_messages"]
profiles_collection = fridgechef_db["taste_profiles"]

# Helper: serialize MongoDB document
def serialize_doc(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to FridgeChef Recipe API"}

# Search route
@app.get("/search", summary="Search recipes by keyword")
def search_recipes(
    query: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(5, ge=1, le=100, description="Max number of results"),
):
    regex = {"$regex": query, "$options": "i"}
    cursor = recipes_collection.find(
        {
            "$or": [
                {"NER": regex},
                {"ingredients": regex},
                {"directions": regex},
                {"title": regex},
            ]
        }
    ).limit(limit)
    return [serialize_doc(doc) for doc in cursor]

# Get recipe by ObjectId
@app.get("/recipes/{id}", summary="Get a recipe by its MongoDB ObjectId")
def get_recipe(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    doc = recipes_collection.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return serialize_doc(doc)

# --- NEW ENDPOINTS ---

# POST review
@app.post("/reviews", summary="Add a new review")
def add_review(review: dict = Body(...)):
    review["date"] = datetime.utcnow()
    result = reviews_collection.insert_one(review)
    return {"message": "Review added", "id": str(result.inserted_id)}

# GET reviews for recipe
@app.get("/reviews/{recipeId}", summary="Get reviews for a recipe")
def get_reviews(recipeId: str):
    docs = reviews_collection.find({"recipeId": recipeId})
    return [serialize_doc(doc) for doc in docs]

# POST important message
@app.post("/important-messages", summary="Save an important message")
def add_message(message: dict = Body(...)):
    message["timestamp"] = datetime.utcnow()
    result = messages_collection.insert_one(message)
    return {"message": "Message saved", "id": str(result.inserted_id)}

# GET important messages for user
@app.get("/important-messages/{userId}", summary="Get important messages for a user")
def get_messages(userId: str):
    docs = messages_collection.find({"userId": userId})
    return [serialize_doc(doc) for doc in docs]

# POST taste profile
@app.post("/taste-profiles", summary="Save or update a taste profile")
def save_taste_profile(profile: dict = Body(...)):
    profile["lastUpdated"] = datetime.utcnow()
    profiles_collection.update_one(
        {"userId": profile["userId"]},
        {"$set": profile},
        upsert=True
    )
    return {"message": "Taste profile saved or updated"}

# GET taste profile for user
@app.get("/taste-profiles/{userId}", summary="Get a user's taste profile")
def get_taste_profile(userId: str):
    profile = profiles_collection.find_one({"userId": userId})
    if not profile:
        raise HTTPException(status_code=404, detail="Taste profile not found")
    return serialize_doc(profile)
