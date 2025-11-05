from uuid import uuid4
from datetime import date
from pydantic import BaseModel, Field, condecimal, constr
from typing import Optional


class ExpenditureModel(BaseModel):
    name: constr(max_length=255, strict=True) = Field(description="Name or brief description of the expense.")
    date_of_expense: date = Field(description="The date the expense was incurred (YYYY-MM-DD).") 
    amount: condecimal(max_digits=10, decimal_places=2) = Field(description="The amount of the expense (positive for income, negative for debit).")
    category: Optional[constr(max_length=50, strict=True)] = Field(None, description="The category of the expense (e.g., 'Groceries', 'Travel').")
    notes: Optional[str] = Field(None, description="Detailed notes or description (TEXT field equivalent).")
    status: constr(max_length=20, strict=True) = Field('Pending', description="The current status of the expense (e.g., 'Paid', 'Pending', 'Reimbursed').")