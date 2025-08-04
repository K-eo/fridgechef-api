from fastapi import FastAPI, Query
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

app = FastAPI()

# Allow cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mongo setup
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database()  # will work if URI ends with /recipes_list
collection = db["recipes_data"]

@app.get("/search")
def search(query: str = Query(...), limit: int = 5):
    regex = {"$regex": query, "$options": "i"}  # case-insensitive search
    results = collection.find(
        {
            "$or": [
                {"NER": regex},
                {"ingredients": regex},
                {"title": regex},
            ]
        }
    ).limit(limit)
    return list(results)
