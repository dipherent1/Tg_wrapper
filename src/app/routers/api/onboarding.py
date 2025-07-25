# app/routers/onboarding.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...core.listener.telethon_client import get_telethon_client

router = APIRouter()

# --- Pydantic Models for Request Bodies ---
class OnboardStartRequest(BaseModel):
    session_name: str
    phone_number: str

class OnboardCompleteRequest(BaseModel):
    session_name: str
    phone_number: str
    code: str
    password: str = "" # 2FA password, optional

# This is a simple in-memory store for the phone_code_hash.
# In production, use Redis or a database for this.
ONBOARDING_SESSIONS = {}

@router.post("/onboard/start")
async def onboard_start(request: OnboardStartRequest):
    """Step 1: Send the confirmation code to the user's phone."""
    client = get_telethon_client(request.session_name)
    try:
        await client.connect()
        sent_code = await client.send_code_request(request.phone_number)
        ONBOARDING_SESSIONS[request.session_name] = sent_code.phone_code_hash
        await client.disconnect()
        return {"message": "Verification code sent successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/onboard/complete")
async def onboard_complete(request: OnboardCompleteRequest):
    """Step 2: Complete the login with the code and optional 2FA password."""
    client = get_telethon_client(request.session_name)
    phone_code_hash = ONBOARDING_SESSIONS.get(request.session_name)

    if not phone_code_hash:
        raise HTTPException(status_code=400, detail="Onboarding process not started or expired.")

    try:
        await client.connect()
        await client.sign_in(
            request.phone_number,
            request.code,
            phone_code_hash=phone_code_hash
        )
    except Exception as e:
         # Handle 2FA password if required
        if "password" in str(e).lower():
            if not request.password:
                raise HTTPException(status_code=401, detail="Two-factor authentication required.")
            await client.sign_in(password=request.password)
        else:
            raise HTTPException(status_code=400, detail=str(e))
            
    # Cleanup and confirm
    del ONBOARDING_SESSIONS[request.session_name]
    me = await client.get_me()
    await client.disconnect()
    
    # You would now add this user to your USER_SETTINGS in config.py or your database
    return {"message": f"Successfully onboarded user {me.first_name}. Please restart the service to begin listening."}