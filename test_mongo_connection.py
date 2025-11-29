import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.mongodb_utils import get_mongodb_manager

# Get MongoDB manager
manager = get_mongodb_manager()
client = manager._client
db = manager._db

print("=" * 60)
print("MONGODB CONNECTION DETAILS")
print("=" * 60)
print(f"Client: {client}")
print(f"Database name: {db.name}")
print(f"Database: {db}")
print(f"Full database names: {client.list_database_names()}")
print(f"\nCollections in '{db.name}':")
for collection_name in db.list_collection_names():
    count = db[collection_name].count_documents({})
    print(f"  - {collection_name}: {count} documents")

print(f"\nPatients collection details:")
patients_coll = db.patients
print(f"  Full name: {patients_coll.full_name}")
print(f"  Database: {patients_coll.database.name}")
print(f"  Count: {patients_coll.count_documents({})}")

# List actual patient documents
print(f"\nActual patients:")
for p in patients_coll.find({}, {"tokenNumber": 1, "name": 1}):
    print(f"  Token #{p['tokenNumber']}: {p['name']}")
