from pymongo import MongoClient
import certifi
import os
from datetime import datetime

MONGODB_URL = "mongodb+srv://udaya1:udaya1@cluster0.ub6jv.mongodb.net/"
DATABASE_NAME = "MovieCloud_Airswift1"
DATABASE_NAME = "MovieCloud_Airswift"

def list_patients():
    try:
        print("Connecting to MongoDB...")
        client = MongoClient(MONGODB_URL, tlsCAFile=certifi.where())
        db = client[DATABASE_NAME]
        print("\n----- BOOKINGS -----")
        try:
            bookings_coll = db["bookings"]
            count = bookings_coll.count_documents({})
            print(f"Total Bookings: {count}")
            if count > 0:
                sample = bookings_coll.find_one()
                print("Sample Booking:")
                # Convert ObjectId to str for printing
                sample["_id"] = str(sample["_id"])
                if "patient_id" in sample: sample["patient_id"] = str(sample["patient_id"])
                print(sample)
        except Exception as e:
            print(f"Error reading bookings: {e}")
        patients_col = db["patients"]
        
        count = patients_col.count_documents({})
        print(f"\n✅ Connected! Total Patients in DB: {count}")
        
        if count > 0:
            print("\nLast 5 Patients:")
            for p in patients_col.find().sort("_id", -1).limit(5):
                print(f"- Name: {p.get('full_name')}, ID: {p.get('_id')}, CreatedBy: {p.get('created_by')}")
        else:
            print("❌ No patients found in the database.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_patients()
