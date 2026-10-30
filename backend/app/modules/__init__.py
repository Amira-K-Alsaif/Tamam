from app.modules.career.router import router as career_router
from app.modules.chat.router import router as chat_router
from app.modules.knowledge.router import router as knowledge_router
from app.modules.onboarding.router import router as onboarding_router
from app.modules.org_map.router import router as org_map_router
from app.modules.procedures.router import router as procedures_router

ROUTERS = [
    chat_router,
    knowledge_router,
    procedures_router,
    org_map_router,
    onboarding_router,
    career_router,
]
