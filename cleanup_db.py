from database.connection import get_collection, connect_to_mongo
from bson import ObjectId

def cleanup_sample_data():
    if not connect_to_mongo():
        print("❌ Failed to connect to database")
        return

    bookings_collection = get_collection("bookings")
    patients_collection = get_collection("patients")

    # Sample MRNs from init_db.py
    sample_mrns = ["MRN001", "MRN002", "MRN003"]
    
    print("🧹 Cleaning up sample patients...")
    patient_result = patients_collection.delete_many({"medical_record_number": {"$in": sample_mrns}})
    print(f"✅ Deleted {patient_result.deleted_count} sample patients")

    print("🧹 Cleaning up bookings with 'Unknown Patient' or from sample data...")
    # This will catch the ones created by init_db.py which use MRN001 (John Smith)
    # But since we might have already deleted the patient, we can also look for the specific locations
    sample_locations = ["City General Hospital", "Regional Trauma Center"]
    booking_result = bookings_collection.delete_many({
        "$or": [
            {"pickup_location": {"$in": sample_locations}},
            {"destination": {"$in": sample_locations}}
        ]
    })
    print(f"✅ Deleted {booking_result.deleted_count} sample bookings")

if __name__ == "__main__":
    cleanup_sample_data()
