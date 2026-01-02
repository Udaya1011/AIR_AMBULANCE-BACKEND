
from database.connection import connect_to_mongo, get_collection, close_mongo_connection
from bson import ObjectId
import sys
import os

# Add current directory to path so we can import from database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_all_patient_ids():
    if not connect_to_mongo():
        print("Could not connect to database")
        return

    try:
        patients_collection = get_collection("patients")
        hospitals_collection = get_collection("hospitals")
        
        patients = list(patients_collection.find({}))
        print(f"Found {len(patients)} patients")
        
        hospital_counts = {}
        gen_count = 0
        
        for p in patients:
            h_id = p.get("assigned_hospital_id")
            
            if h_id and ObjectId.is_valid(h_id):
                hospital = hospitals_collection.find_one({"_id": ObjectId(h_id)})
                if hospital:
                    h_name = hospital.get("hospital_name", "HOSP")
                    prefix = h_name.split()[0].upper()
                    
                    if h_id not in hospital_counts:
                        hospital_counts[h_id] = 0
                    hospital_counts[h_id] += 1
                    
                    new_id = f"{prefix}-{str(hospital_counts[h_id]).zfill(3)}"
                else:
                    gen_count += 1
                    new_id = f"GEN-{str(gen_count).zfill(3)}"
            else:
                gen_count += 1
                new_id = f"GEN-{str(gen_count).zfill(3)}"
            
            patients_collection.update_one(
                {"_id": p["_id"]},
                {"$set": {"patient_id": new_id}}
            )
            print(f"Updated patient {p.get('full_name', 'Unknown')} with ID {new_id}")
            
        print("✅ Finished updating all patient IDs")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_mongo_connection()

if __name__ == "__main__":
    update_all_patient_ids()
