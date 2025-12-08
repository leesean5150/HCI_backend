from pydantic import BaseModel, Field, EmailStr
from datetime import date
from typing import Optional
from uuid import UUID
from typing import List

# Users
class WebExpUser(BaseModel):
    user_id: str

class WebExpUserCreate(WebExpUser):
    pass

# Tasks
class WebExpTask(BaseModel):
    task_id: str
    user_id: str
    task_number: int
    time_taken_seconds: Optional[int] = None
    question1: Optional[int] = None
    question2: Optional[int] = None
    device_type: Optional[str] = None  # "mobile" or "desktop"

class WebExpTaskCreate(BaseModel):
    user_id: str
    task_number: int
    time_taken_seconds: Optional[int] = None
    device_type: Optional[str] = None  # "mobile" or "desktop"

class WebExpTaskUpdateTime(BaseModel):
    # Support both task_id OR user_id + task_number
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    task_number: Optional[int] = None
    time_taken_seconds: int

class WebExpTaskUpdateQuestions(BaseModel):
    # Support both task_id OR user_id + task_number
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    task_number: Optional[int] = None
    question1: int
    question2: int

# Expenditures
class WebExpExpenditure(BaseModel):
    uuid: str
    task_id: str
    name: str
    date_of_expense: date
    amount: float
    category: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "Pending"

class WebExpExpenditureCreate(BaseModel):
    user_id: str
    task_number: int
    name: str
    date_of_expense: date
    amount: float
    category: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class WebExpExpenditureBulkItem(BaseModel):
    name: str
    date_of_expense: date
    amount: float
    category: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

    




class WebExpTaskOut(WebExpTask):
    expenditures: List[WebExpExpenditure] = []

class WebExpUserOut(WebExpUser):
    tasks: List[WebExpTaskOut] = []