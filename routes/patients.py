from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from database.connection import get_collection
from models.patient import Patient, PatientCreate, PatientUpdate, AcuityLevel
from models.user import User, UserRole
from routes.auth import get_current_active_user
from bson import ObjectId
from typing import Annotated
from datetime import datetime, date
import logging
import json

router = APIRouter(prefix="/api/patients", tags=["patients"])
logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

async def update_hospital_occupancy(hospital_id: str, increment: int):
    """Helper to update hospital occupied_beds count"""
    if not hospital_id or not ObjectId.is_valid(hospital_id):
        return
    
    try:
        hospitals_collection = get_collection("hospitals")
        hospitals_collection.update_one(
            {"_id": ObjectId(hospital_id)},
            {"$inc": {"occupied_beds": increment}}
        )
    except Exception as e:
        logger.error(f"Error updating hospital occupancy: {e}")

# =====================================================
# CREATE PATIENT
# =====================================================
@router.post("", response_model=Patient)
async def create_patient(
    patient_data: PatientCreate,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    allowed_roles = [
        UserRole.SUPERADMIN,
        UserRole.DISPATCHER,
        UserRole.HOSPITAL_STAFF,
        UserRole.DOCTOR,
    ]

    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        patients_collection = get_collection("patients")

        patient_dict = json.loads(patient_data.json())

        # Convert date_of_birth → datetime
        if patient_dict.get("date_of_birth"):
            patient_dict["date_of_birth"] = datetime.fromisoformat(patient_dict["date_of_birth"])

        patient_dict["created_at"] = patient_dict["updated_at"] = datetime.utcnow()
        patient_dict["created_by"] = str(current_user.id)

        # Generate custom patient_id
        hospital_id = patient_dict.get("assigned_hospital_id")
        if hospital_id and ObjectId.is_valid(hospital_id):
            hospitals_collection = get_collection("hospitals")
            hospital = hospitals_collection.find_one({"_id": ObjectId(hospital_id)})
            if hospital:
                # Use first word of hospital name as prefix
                h_name = hospital.get("hospital_name", "HOSP")
                prefix = h_name.split()[0].upper()
                # Count current patients for this hospital
                count = patients_collection.count_documents({"assigned_hospital_id": hospital_id})
                patient_dict["patient_id"] = f"{prefix}-{str(count + 1).zfill(3)}"
            else:
                patient_dict["patient_id"] = f"PAT-{str(patients_collection.count_documents({}) + 1).zfill(3)}"
        else:
            patient_dict["patient_id"] = f"GEN-{str(patients_collection.count_documents({}) + 1).zfill(3)}"

        result = patients_collection.insert_one(patient_dict)
        inserted = patients_collection.find_one({"_id": result.inserted_id})

        if not inserted:
            raise HTTPException(status_code=500, detail="Failed to retrieve inserted patient")

        # Update hospital occupancy if assigned
        if patient_dict.get("assigned_hospital_id"):
            await update_hospital_occupancy(patient_dict["assigned_hospital_id"], 1)

        inserted["id"] = str(inserted["_id"])

        if isinstance(inserted.get("date_of_birth"), datetime):
            inserted["date_of_birth"] = inserted["date_of_birth"].date()

        # Ensure defaults for missing fields to prevent crashes when creating a new patient
        # This is defensive programming, as PatientCreate should ensure these are present or have defaults
        if "weight_kg" not in inserted: inserted["weight_kg"] = 0
        if "gender" not in inserted: inserted["gender"] = "other"
        if "acuity_level" not in inserted: inserted["acuity_level"] = "stable"
        if "diagnosis" not in inserted: inserted["diagnosis"] = "Unknown"
        if "allergies" not in inserted: inserted["allergies"] = []

        return Patient(**inserted)

    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail="Error creating patient")


# =====================================================
# GET ALL PATIENTS
# =====================================================
@router.get("", response_model=List[Patient])
async def get_patients(
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    acuity_level: Optional[AcuityLevel] = None
):
    try:
        patients_collection = get_collection("patients")
        query = {}

        if acuity_level:
            query["acuity_level"] = acuity_level.value

        cursor = patients_collection.find(query).skip(skip).limit(limit)

        patients = []
        for patient in cursor:
            try:
                patient_dict = dict(patient)
                patient_dict["id"] = str(patient["_id"])

                if isinstance(patient_dict.get("date_of_birth"), datetime):
                    patient_dict["date_of_birth"] = patient_dict["date_of_birth"].date()
                
                # Ensure defaults for missing fields to prevent crashes
                if "weight_kg" not in patient_dict: patient_dict["weight_kg"] = 0
                if "gender" not in patient_dict: patient_dict["gender"] = "other"
                if "acuity_level" not in patient_dict: patient_dict["acuity_level"] = "stable"
                if "diagnosis" not in patient_dict: patient_dict["diagnosis"] = "Unknown"
                if "allergies" not in patient_dict: patient_dict["allergies"] = []
                
                patients.append(Patient(**patient_dict))
            except Exception as e:
                print(f"Skipping bad patient record: {patient.get('_id', 'unknown')} - Error: {e}")
                continue

        return patients

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error getting patients: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving patients")


# =====================================================
# GET PATIENT BY ID
# =====================================================
@router.get("/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient ID")

    try:
        patients_collection = get_collection("patients")
        patient = patients_collection.find_one({"_id": ObjectId(patient_id)})

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        patient["id"] = str(patient["_id"])

        if isinstance(patient.get("date_of_birth"), datetime):
            patient["date_of_birth"] = patient["date_of_birth"].date()

        return Patient(**patient)

    except Exception:
        raise HTTPException(status_code=500, detail="Error retrieving patient")


# =====================================================
# UPDATE PATIENT
# =====================================================
@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    allowed_roles = [
        UserRole.SUPERADMIN,
        UserRole.DISPATCHER,
        UserRole.HOSPITAL_STAFF,
        UserRole.DOCTOR,
    ]

    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient ID")

    try:
        patients_collection = get_collection("patients")
        existing = patients_collection.find_one({"_id": ObjectId(patient_id)})

        if not existing:
            raise HTTPException(status_code=404, detail="Patient not found")

        update_data = patient_update.dict(exclude_unset=True)

        # Handle nested objects
        for key, value in update_data.items():
            if hasattr(value, "dict"):
                update_data[key] = value.dict()

        # Convert date_of_birth
        if update_data.get("date_of_birth"):
            dob = update_data["date_of_birth"]
            if isinstance(dob, date):
                update_data["date_of_birth"] = datetime.combine(dob, datetime.min.time())
            else:
                update_data["date_of_birth"] = datetime.fromisoformat(dob)

        update_data["updated_at"] = datetime.utcnow()

        # Handle hospital occupancy change
        old_hospital_id = existing.get("assigned_hospital_id")
        new_hospital_id = update_data.get("assigned_hospital_id")

        if old_hospital_id != new_hospital_id:
            if old_hospital_id:
                await update_hospital_occupancy(old_hospital_id, -1)
            if new_hospital_id:
                await update_hospital_occupancy(new_hospital_id, 1)
                
                # Regenerate patient_id for the new hospital
                hospitals_collection = get_collection("hospitals")
                hospital = hospitals_collection.find_one({"_id": ObjectId(new_hospital_id)})
                if hospital:
                    h_name = hospital.get("hospital_name", "HOSP")
                    prefix = h_name.split()[0].upper()
                    count = patients_collection.count_documents({"assigned_hospital_id": new_hospital_id})
                    update_data["patient_id"] = f"{prefix}-{str(count + 1).zfill(3)}"
            elif old_hospital_id and not new_hospital_id:
                # If unassigned, change to GEN prefix
                count = patients_collection.count_documents({"assigned_hospital_id": None})
                update_data["patient_id"] = f"GEN-{str(count + 1).zfill(3)}"

        patients_collection.update_one({"_id": ObjectId(patient_id)}, {"$set": update_data})

        updated = patients_collection.find_one({"_id": ObjectId(patient_id)})
        updated["id"] = str(updated["_id"])

        if isinstance(updated.get("date_of_birth"), datetime):
            updated["date_of_birth"] = updated["date_of_birth"].date()

        return Patient(**updated)

    except Exception:
        raise HTTPException(status_code=500, detail="Error updating patient")


# =====================================================
# DELETE PATIENT (NEW)
# =====================================================
@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    allowed_roles = [
        UserRole.SUPERADMIN,
        UserRole.DISPATCHER,
        UserRole.HOSPITAL_STAFF,
        UserRole.DOCTOR,
    ]

    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not ObjectId.is_valid(patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient ID")

    try:
        patients_collection = get_collection("patients")
        existing = patients_collection.find_one({"_id": ObjectId(patient_id)})
        
        result = patients_collection.delete_one({"_id": ObjectId(patient_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Update hospital occupancy if patient was assigned
        if existing and existing.get("assigned_hospital_id"):
            await update_hospital_occupancy(existing["assigned_hospital_id"], -1)

        return {"message": "Patient deleted successfully"}

    except Exception:
        raise HTTPException(status_code=500, detail="Error deleting patient")


# =====================================================
# CRITICAL COUNT
# =====================================================
@router.get("/critical/count")
async def get_critical_patients_count(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        patients_collection = get_collection("patients")
        count = patients_collection.count_documents({"acuity_level": "critical"})
        return {"critical_patients_count": count}
    except Exception:
        raise HTTPException(status_code=500, detail="Error getting critical patients count")
