from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import auth, email, telegram  # ✅ Import groupé propre

app = FastAPI()

# Inclusion des routes avec ou sans préfixe
app.include_router(auth.router, prefix="/auth")
app.include_router(email.router, prefix="/email")
app.include_router(telegram.router)  # ✅ webhook reste accessible via /webhook

# Configuration CORS : autoriser frontend local + production
origins = [
    "http://localhost:5173",  # Développement local
    "https://blackcoin-v5-frontend.vercel.app"  # Frontend Vercel
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
