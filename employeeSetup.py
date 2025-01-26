from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random
import gridfs
import os
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
def get_database():
 
    client = MongoClient(MONGO_URI)
    return client['pdf_db'],gridfs.GridFS(client["pdf_db"])

def create_employee_schema(db):
    db.create_collection("basic_info")
    db.create_collection("employment_details")
    db.create_collection("payroll")
    db.create_collection("leaves")
    db.create_collection("reimbursement_claims")
    db.create_collection("attendance")
    db.create_collection("roles")
    db.create_collection("documents")
    db.create_collection("gosi")

def generate_dummy_data(fs):
    employee_id = "E001"
    
    basic_info = {
        "employeeId": employee_id,
        "fullName": "Shanawaz Khan",
        "gender": "Male",
        "dateOfBirth": "1990-01-01",
        "nationality": "Saudi",
        "maritalStatus": "Single",
        "email": "shanawazkhan@example.com",
        "phone": "1234567890",
        "address": "234 King Abdulaziz Road, Al Olaya District, Riyadh 12241, Saudi Arabia"
    }

    employment_details = {
        "employeeId": employee_id,
        "joiningDate": "2023-01-15",
        "department": "IT",
        "designation": "Software Engineer",
        "employmentType": "Permanent",
        "workLocation": "On-site",
        "managerId": "M001",
        "probationEndDate": "2023-07-15",
        "employmentStatus": "Active"
    }

    payroll = {
        "employeeId": employee_id,
        "basicSalary": 5000,
        "housingAllowance": 1500,
        "transportationAllowance": 500,
        "overtimeRate": 20,
        "bankAccount": {
            "bankName": "Bank of America",
            "accountNumber": "123456789012",
            "IBAN": "US12345678901234567890"
        },
        "GOSIStatus": True,
        "GOSIContribution": {
            "employeeShare": 0.09,
            "employerShare": 0.11
        },
        "taxDetails": {
            "taxableIncome": 6500,
            "taxDeductions": 1000
        },
        "paymentCycle": "Monthly"
    }

    leave_history = []
    for i in range(3):
        start_date = datetime(2024, 1, 10) + timedelta(days=i * 15)
        leave_history.append({
            "leaveId": f"L{i+1}",
            "leaveType": "Annual",
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": (start_date + timedelta(days=2)).strftime("%Y-%m-%d"),
            "status": "Approved"
        })

    leaves = {
        "employeeId": employee_id,
        "annualLeaveEntitlement": 20,
        "sickLeaveEntitlement": 10,
        "remainingAnnualLeave": 17,
        "leaveHistory": leave_history
    }

    reimbursement_claims = {
        "employeeId": employee_id,
        "expenseClaims": [
            {
                "claimId": "C001",
                "date": "2024-01-05",
                "amount": 200,
                "category": "Travel",
                "status": "Approved",
                "approvedBy": "M001"
            },
            {
                "claimId": "C002",
                "date": "2024-01-20",
                "amount": 50,
                "category": "Food",
                "status": "Pending",
                "approvedBy": ""
            }
        ]
    }

    attendance_records = []
    for i in range(30):
        date = datetime(2024, 1, 1) + timedelta(days=i)
        check_in = datetime(date.year, date.month, date.day, 9, 0)
        check_out = datetime(date.year, date.month, date.day, 17, 0)
        attendance_records.append({
            "date": date.strftime("%Y-%m-%d"),
            "checkInTime": check_in.strftime("%Y-%m-%dT%H:%M:%S"),
            "checkOutTime": check_out.strftime("%Y-%m-%dT%H:%M:%S"),
            "hoursWorked": 8,
            "overtimeHours": random.choice([0, 1, 2])
        })

    attendance = {
        "employeeId": employee_id,
        "attendanceRecords": attendance_records,
        "totalOvertimeHours": sum([rec["overtimeHours"] for rec in attendance_records])
    }

    role = {
        "employeeId": employee_id,
        "role": "Employee",
        "permissions": ["ViewPayroll", "ApplyLeave"]
    }

    documents = {
        "employeeId": employee_id,
        "documents": []
    }
    critical_files = {
        "Contract": "contract.pdf",
        "OfferLetter": "ol.pdf",
        "PerformanceReview": "pr.pdf",
    }
    for doc_type , file_path in critical_files.items():
        with open(file_path,"rb")as file:
            file_id = fs.put(file, filename=os.path.basename(file_path))
            documents["documents"].append({
                "documentType": doc_type,
                "fileId": str(file_id),
                "uploadedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            })

    gosi_contributions = []
    for i in range(2):
        gosi_contributions.append({
            "month": (datetime(2024, 1, 1) + timedelta(days=i * 30)).strftime("%Y-%m"),
            "employeeContribution": 450,
            "employerContribution": 550
        })

    gosi = {
        "employeeId": employee_id,
        "GOSIId": "G123456",
        "GOSIStartDate": "2023-01-15",
        "GOSIContributions": gosi_contributions
    }

    return {
        "basic_info": basic_info,
        "employment_details": employment_details,
        "payroll": payroll,
        "leaves": leaves,
        "reimbursement_claims": reimbursement_claims,
        "attendance": attendance,
        "roles": role,
        "documents": documents,
        "gosi": gosi
    }

def upload_dummy_data(db, dummy_data):
    for collection, data in dummy_data.items():
        db[collection].insert_one(data)

if __name__ == "__main__":
    db,fs = get_database()
    print("Db done")
    create_employee_schema(db)
    print("schema done")
    dummy_data = generate_dummy_data(fs)
    upload_dummy_data(db, dummy_data)
    print("Dummy data uploaded successfully.")
