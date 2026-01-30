from pymongo import MongoClient

mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["github_webhooks"]
events_collection = db["events"]