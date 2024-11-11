from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# MySQL database connection string
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/employee_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
