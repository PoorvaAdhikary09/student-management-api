from fastapi import FastAPI, HTTPException, status
# from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from typing import Optional, List
import random
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all origins (for development only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Atlas connection - USING YOUR CREDENTIALS
MONGODB_URL = "mongodb+srv://Poorva:123@firstcluster.arfxwud.mongodb.net/"
client = MongoClient(MONGODB_URL)
db = client.Student  # Exactly matching your Compass database name
students_collection = db.StudentDetails  # Assuming collection is called 'students'
# Add this during startup
students_collection.create_index("student_id", unique=True)

# Pydantic model
class Student(BaseModel):
    student_id:Optional[int] = None
    name: str
    age: int
    grade: str
    email: str
    
# Generate random student ID
def generate_student_id():
    return random.randint(1, 199)

@app.get("/")
async def root():
    return {"message": "Student API is running. Access /students endpoint"}

# GET
@app.get("/students/")
async def get_all_students():
    students = []
    cursor = students_collection.find({})
    for doc in cursor:
        # Convert document to match your Pydantic model
        students.append( {
            "_id": str(doc["_id"]),  # Convert ObjectId to string
            "student_id": doc["student_id"],
            "name": doc["name"],
            "age": doc["age"],
            "grade": doc["grade"],
            "email": doc["email"]
        })
    return students

# GET by ID
@app.get("/students/{student_id}", response_model=Student)
async def get_student(student_id: int):
    student = students_collection.find_one({"student_id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Convert ObjectId to string
    student["_id"] = str(student["_id"])
    return student

# CREATE
@app.post("/students/", response_model=Student, status_code=201)
async def create_student(student: Student):
      # Generate ID if not provided
    if not student.student_id:
        student.student_id = generate_student_id()
    
    # Check if ID already exists
    if students_collection.find_one({"student_id": student.student_id}):
        raise HTTPException(status_code=400, detail="Student ID already exists")
    
    students_collection.insert_one(student.dict())
    return student

# Delete
# DELETE
@app.delete("/students/{student_id}", status_code=204)
async def delete_student(student_id: int):
    result = students_collection.delete_one({"student_id": student_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

# UPDATE
@app.put("/students/{student_id}", response_model=Student)
async def update_student(student_id: int, student: Student):
    result = students_collection.update_one(
        {"student_id": student_id},
        {"$set": student.dict(exclude={"student_id"})}  # Prevent ID change
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return student