# backend/routes/email.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict
from backend.utils.email_utils import send_verification_email  # on garde une seule fonction

router = APIRouter(prefix="/email")  # Préfixe propre

# Modèle pour les données entrantes
class EmailRequest(BaseModel):
    email: EmailStr
    code: str

@router.post("/send-validation-email", response_model=Dict[str, str])
async def send_email(data: EmailRequest):
    try:
        # Envoi du mail (fonction non async donc pas besoin de "await")
        success = send_verification_email(data.email, data.code)
        if success:
            return {"message": "Email envoyé avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
