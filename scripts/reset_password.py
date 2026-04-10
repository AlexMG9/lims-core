"""
Development utility: generate bcrypt hash for a password.

Usage (inside the lims_api container):
    docker exec -it lims_api python /app/scripts/reset_password.py

Prompts for a password (hidden input) and prints the corresponding
bcrypt hash. Useful for manually resetting the admin password in the
database or for seeding new users with known credentials during
development.

NOT intended for production use.
"""
from getpass import getpass
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password = getpass("Password to hash: ")
if not password:
    print("Error: password cannot be empty.")
    exit(1)

print(pwd_context.hash(password))
