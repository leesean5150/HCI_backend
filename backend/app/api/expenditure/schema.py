from datetime import date
from pydantic import BaseModel, Field, condecimal, constr
from typing import Optional
from decimal import Decimal


class ExpenditureModel(BaseModel):
    name: constr(max_length=255, strict=True) = Field(description="Name or brief description of the expense.")
    date_of_expense: date = Field(description="The date the expense was incurred (YYYY-MM-DD).") 
    amount: condecimal(max_digits=10, decimal_places=2) = Field(description="The amount of the expense (positive for income, negative for debit).")
    category: Optional[constr(max_length=50, strict=True)] = Field(None, description="The category of the expense (e.g., 'Groceries', 'Travel').")
    notes: Optional[str] = Field(None, description="Detailed notes or description (TEXT field equivalent).")
    status: constr(max_length=20, strict=True) = Field('Pending', description="The current status of the expense (e.g., 'Approved', 'Pending').")

class ExpenditureUpdateModel(BaseModel):
    name: Optional[str] = None
    date_of_expense: Optional[date] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    # This model_config ensures at least one value is provided (prevents empty {} payloads)
    model_config = {
        "extra": "forbid",
        "min_anystr_length": 1 
    }