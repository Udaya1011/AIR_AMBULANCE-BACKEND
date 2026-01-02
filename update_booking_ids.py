
from database.connection import connect_to_mongo, get_collection, close_mongo_connection
from bson import ObjectId
import sys
import os

# Add current directory to path so we can import from database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_all_booking_ids():
    if not connect_to_mongo():
        print("Could not connect to database")
        return

    try:
        bookings_collection = get_collection("bookings")
        hospitals_collection = get_collection("hospitals")
        
        bookings = list(bookings_collection.find({}))
        print(f"Found {len(bookings)} bookings")
        
        hospital_counts = {}
        gen_count = 0
        
        for b in bookings:
            if b.get("booking_id"):
                print(f"Booking {b['_id']} already has a booking_id: {b['booking_id']}")
                continue
                
            origin_h_id = b.get("origin_hospital_id")
            
            if origin_h_id and ObjectId.is_valid(origin_h_id):
                hospital = hospitals_collection.find_one({"_id": ObjectId(origin_h_id)})
                if hospital:
                    h_name = hospital.get("hospital_name", "HOSP")
                    prefix = h_name.split()[0].upper()
                    
                    if origin_h_id not in hospital_counts:
                        hospital_counts[origin_h_id] = 0
                    hospital_counts[origin_h_id] += 1
                    
                    new_id = f"BK-{prefix}-{str(hospital_counts[origin_h_id]).zfill(3)}"
                else:
                    gen_count += 1
                    new_id = f"BK-GEN-{str(gen_count).zfill(3)}"
            else:
                gen_count += 1
                new_id = f"BK-GEN-{str(gen_count).zfill(3)}"
            
            bookings_collection.update_one(
                {"_id": b["_id"]},
                {"$set": {"booking_id": new_id}}
            )
            print(f"Updated booking {b['_id']} with ID {new_id}")
            
        print("✅ Finished updating all booking IDs")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_mongo_connection()

if __name__ == "__main__":
    update_all_booking_ids()
