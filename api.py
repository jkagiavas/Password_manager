from fastapi import FastAPI
from pydantic import BaseModel
from database import Password, session
from cryptography.fernet import Fernet
import os
from jose import jwt
from datetime import datetime, timedelta
from auth import verify_master_password
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import redis

# Σύνδεση στον Redis server (τρέχει τοπικά στην 6379)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"  # The signing algorithm - HS256 is the most common

# oauth2_scheme automatically reads the JWT token from the Authorization header
oauth2_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    # Depends() tells FastAPI to run this function before the endpoint
    # and inject the result as a parameter
    token = credentials.credentials
    try:
        # Decode and verify the token using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# This defines exactly what data we expect when saving a password
# Pydantic will automatically validate incoming requests against this
class PasswordEntry(BaseModel):
    website: str
    email: str
    password: str

#Create the FastAPI application instance
app = FastAPI()
# Serve static files from the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the frontend at /app
@app.get("/app")
def frontend():
    return FileResponse("static/index.html")

@app.get("/")
def home():
    return {"message": "Password Manager API is running"}


# Load the encryption key - same key as main.py so passwords are compatible
KEY_FILE = "secret.key"
with open(KEY_FILE, "rb") as f:
    KEY = f.read()
fernet = Fernet(KEY)


@app.post("/passwords")
def save_password(entry: PasswordEntry, token: dict = Depends(verify_token)):
    # Check if website already exists
    existing = session.query(Password).filter_by(website=entry.website).first()
    if existing:
        raise HTTPException(status_code=400, detail="Website already exists. Use update instead.")

    encrypted = fernet.encrypt(entry.password.encode()).decode()
    new_entry = Password(
        website=entry.website,
        email=entry.email,
        password=encrypted
    )
    session.add(new_entry)
    session.commit()
    return {"message": "Password saved successfully"}


@app.get("/passwords/{website}")
def get_password(website: str, token: dict = Depends(verify_token)):
    # Query the database for the website
    result = session.query(Password).filter_by(website=website).first()

    if result is None:
        # Return a 404 error if website not found
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Website not found")

    # Decrypt the password before returning it
    decrypted = fernet.decrypt(result.password.encode()).decode()

    return {
        "website": result.website,
        "email": result.email,
        "password": decrypted
    }



@app.post("/login")
def login(credentials: dict):
    password = credentials.get("password")

    # --- RATE LIMITING ---
    # Χρησιμοποιούμε ένα σταθερό key γιατί έχουμε έναν μόνο χρήστη (master).
    # Σε multi-user θα ήταν π.χ. f"login_attempts:{username}" ή ανά IP.
    rate_key = "login_attempts:master"

    # Πόσες αποτυχημένες προσπάθειες υπάρχουν ήδη;
    attempts = redis_client.get(rate_key)
    if attempts and int(attempts) >= 5:
        # Πόσα δευτερόλεπτα μένουν μέχρι το ξεμπλοκάρισμα
        ttl = redis_client.ttl(rate_key)
        minutes = ttl // 60
        seconds = ttl % 60
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {minutes}m {seconds}s."
        )

    # --- ΕΛΕΓΧΟΣ PASSWORD ---
    if not verify_master_password(password):
        # Λάθος password → αύξησε τον μετρητή
        redis_client.incr(rate_key)
        # Βάλε expiration 15 λεπτά (μόνο την πρώτη φορά χρειάζεται,
        # αλλά το ξαναβάζουμε για σιγουριά)
        redis_client.expire(rate_key, 900)
        raise HTTPException(status_code=401, detail="Invalid password")

    # --- ΕΠΙΤΥΧΙΑ ---
    # Σωστό password → σβήσε τον μετρητή αποτυχιών
    redis_client.delete(rate_key)

    # Create JWT token that expires in 30 minutes
    expiration = datetime.utcnow() + timedelta(minutes=30)
    token = jwt.encode(
        {"sub": "master", "exp": expiration},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {"access_token": token}