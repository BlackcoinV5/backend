# backend/main.py
from fastapi import FastAPI
from backend.routes import auth, email
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Inclusion unique des routes avec préfixes
app.include_router(auth.router, prefix="/auth")     # /auth/register, /auth/verify
app.include_router(email.router, prefix="/email")   # /email/send-validation-email (ou autre)

# CORS : autoriser le frontend depuis Vercel
origins = [
    "https://blackcoin-v5-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Backend Blackcoin is running 🎉"}
