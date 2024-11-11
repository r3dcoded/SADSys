from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

# Generate hashed password for '1234'
hashed_password = bcrypt.generate_password_hash("1234").decode("utf-8")
print(hashed_password)