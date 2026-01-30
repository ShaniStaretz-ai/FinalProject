from fastapi import FastAPI

from server.users.routes import router as user_router
from server.models.routes import router as models_router
from server.admin.routes import router as admin_router


def register_routers(app: FastAPI) -> None:
    app.include_router(user_router)
    app.include_router(models_router)
    app.include_router(admin_router)
