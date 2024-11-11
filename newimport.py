from datetime import datetime
from your_model_file import db, Employee  # Import the Employee model

# Assuming you already have position_id, schedule_id, and salary_id available
new_employee = Employee(
    employee_id="E001",
    name="Alice Smith",
    position_id=1,
    schedule_id=1,
    salary_id=1,
    site_id=1,
    contact_number="555-6789",
    email="alice@example.com",
    clock_in=datetime.now()
)

db.session.add(new_employee)
db.session.commit()
