
from fastapi import APIRouter
from app.routers.api.subscription_router import subscription_router
from app.routers.api.onboarding import router as onboarding_router
from app.routers.api.message_router import message_router
from app.routers.api.tags_router import tag_router

routers_list = [
    subscription_router,
    onboarding_router,
    message_router,
    tag_router

]

routers = APIRouter(prefix="/api", tags=["API"])

for router in routers_list:
    routers.include_router(router)

def get_routers():
    """
    Returns routers in the application.
    This is useful for FastAPI to include all routes in the app.
    """
    return routers