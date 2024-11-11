from functools import wraps
from flask_bcrypt import Bcrypt
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = '$2b$12$9okLhVvX7bCvBB2OJ3CIKe3De5wghHvaQf8Z68OVp1j8VAAmb/w8S'

bcrypt = Bcrypt(app)
# MySQL database connection string
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/employee_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class PositionType(db.Model):
    __tablename__ = 'position_types'
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False)

class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position_type_id = db.Column(db.Integer, db.ForeignKey('position_types.id'), nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)

class Site(db.Model):
    __tablename__ = 'sites'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    zip_code = db.Column(db.String(10))

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    schedule_name = db.Column(db.String(50), nullable=False)

class Salary(db.Model):
    __tablename__ = 'salaries'
    id = db.Column(db.Integer, primary_key=True)
    hourly_rate = db.Column(db.Float, nullable=False)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    salary_id = db.Column(db.Integer, db.ForeignKey('salaries.id'))
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'))
    contact_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    clock_in = db.Column(db.DateTime)
    clock_out = db.Column(db.DateTime)
    hours_worked = db.Column(db.Float)

# Decorator for login-required routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

    # Create a route for admin login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

# Create a route for admin logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

# Clock In/Out Functions
def clock_in(employee_id):
    """Record the clock-in time for an employee if they exist in the database."""
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return f"Employee ID {employee_id} does not exist."
    
    if employee.clock_in is not None and employee.clock_out is None:
        return f"{employee_id} is already clocked in."

    employee.clock_in = datetime.now()
    db.session.commit()
    return f"{employee_id} clocked in at {employee.clock_in}."

def clock_out(employee_id):
    """Record the clock-out time and calculate hours worked if clocked in."""
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee or employee.clock_in is None:
        return f"{employee_id} has not clocked in yet."
    
    employee.clock_out = datetime.now()
    time_in = employee.clock_in
    time_out = employee.clock_out
    hours_worked = (time_out - time_in).total_seconds() / 3600  # Convert to hours
    employee.hours_worked = hours_worked
    db.session.commit()
    return f"{employee_id} clocked out at {time_out}. Hours worked: {hours_worked:.2f}"

@app.route("/clock", methods=["POST"])
def handle_clock():
    data = request.json
    employee_id = data.get("employeeId")
    action = data.get("action")
    
    if action == "in":
        message = clock_in(employee_id)
    elif action == "out":
        message = clock_out(employee_id)
    else:
        message = "Invalid action. Please enter 'in' to clock in or 'out' to clock out."
    
    return jsonify({"message": message})

@app.route("/receipt/<employee_id>")
def view_receipt(employee_id):
    """Generate a receipt of the employee's clock-in and clock-out information."""
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if employee:
        clock_in_time = employee.clock_in if employee.clock_in else "N/A"
        clock_out_time = employee.clock_out if employee.clock_out else "N/A"
        hours_worked = employee.hours_worked if employee.hours_worked else "N/A"
        return render_template("receipt.html", employee_id=employee_id, 
                               clock_in_time=clock_in_time,
                               clock_out_time=clock_out_time,
                               hours_worked=hours_worked)
    else:
        return f"No record found for employee ID {employee_id}.", 404

@app.route("/")
def home():
    return render_template("index.html")  # Serve the HTML form page

# Routes for the Admin Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    employees = Employee.query.all()
    positions = Position.query.all()
    sites = Site.query.all()
    schedules = Schedule.query.all()
    salaries = Salary.query.all()
    return render_template("dashboard.html", employees=employees, positions=positions, 
                           sites=sites, schedules=schedules, salaries=salaries)

@app.route("/employee/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        new_employee = Employee(
            employee_id=request.form['employee_id'],
            name=request.form['name'],
            address=request.form['address'],
            position_id=request.form['position_id'],
            schedule_id=request.form['schedule_id'],
            salary_id=request.form.get('salary_id'),
            site_id=request.form.get('site_id'),
            contact_number=request.form['contact_number'],
            email=request.form['email']
        )
        db.session.add(new_employee)
        db.session.commit()
        return redirect(url_for('dashboard'))
    positions = Position.query.all()
    schedules = Schedule.query.all()
    salaries = Salary.query.all()
    sites = Site.query.all()
    return render_template("add_employee.html", positions=positions, schedules=schedules,
                           salaries=salaries, sites=sites)

@app.route("/employee/delete/<int:id>")
def delete_employee(id):
    employee = Employee.query.get(id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/employee/update/<int:id>", methods=["GET", "POST"])
def update_employee(id):
    employee = Employee.query.get(id)
    if request.method == "POST":
        employee.name = request.form['name']
        employee.address = request.form['address']
        employee.position_id = request.form['position_id']
        employee.schedule_id = request.form['schedule_id']
        employee.salary_id = request.form.get('salary_id')
        employee.site_id = request.form.get('site_id')
        employee.contact_number = request.form['contact_number']
        employee.email = request.form['email']
        db.session.commit()
        return redirect(url_for('dashboard'))
    positions = Position.query.all()
    schedules = Schedule.query.all()
    salaries = Salary.query.all()
    sites = Site.query.all()
    return render_template("update_employee.html", employee=employee, positions=positions, 
                           schedules=schedules, salaries=salaries, sites=sites)

if __name__ == "__main__":
    app.run(debug=True)
