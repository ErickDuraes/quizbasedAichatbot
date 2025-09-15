import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini SDK
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory user database
USERS_DB = {}  # {username: {password, score, persona}}

# Request models
class SignupReq(BaseModel):
    username: str
    password: str

class LoginReq(BaseModel):
    username: str
    password: str

class QuizReq(BaseModel):
    username: str
    answers: list[int]

class ChatReq(BaseModel):
    username: str
    message: str

# -------------------------------
# Signup endpoint (optional)
@app.post("/api/signup")
def signup(req: SignupReq):
    if req.username in USERS_DB:
        raise HTTPException(status_code=400, detail="Username already exists")
    USERS_DB[req.username] = {"password": req.password, "score": 0, "persona": "Beginner"}
    return {"message": "Signup successful"}

# Login endpoint (optional)
@app.post("/api/login")
def login(req: LoginReq):
    user = USERS_DB.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}

# Quiz submission endpoint
@app.post("/api/quiz")
def submit_quiz(req: QuizReq):
    score = sum(req.answers)
    if score >= 8:
        persona = "Best"
    elif score >= 4:
        persona = "Average"
    else:
        persona = "Beginner"

    # Auto-create user if not found
    if req.username not in USERS_DB:
        USERS_DB[req.username] = {"password": "", "score": score, "persona": persona}
    else:
        USERS_DB[req.username]["score"] = score
        USERS_DB[req.username]["persona"] = persona

    return {"score": score, "persona": persona}

# Chat endpoint
@app.post("/api/chat")
def chat(req: ChatReq):
    user = USERS_DB.get(req.username)
    if not user:
        # Auto-create guest user with default persona
        USERS_DB[req.username] = {"password": "", "score": 0, "persona": "Beginner"}
        user = USERS_DB[req.username]

    persona_prompts = {
        "Best": "You are an expert scientist. Answer formally with technical depth.",
        "Average": "You are knowledgeable. Answer clearly and simply.",
        "Beginner": "Explain like the user is totally new. Avoid jargon."
    }

    system_prompt = persona_prompts.get(user["persona"], "Casual")

    response = model.generate_content(
        contents=[{"parts": [{"text": f"SYSTEM: {system_prompt}\nUSER: {req.message}"}]}]
    )

    return {"reply": response.text}
