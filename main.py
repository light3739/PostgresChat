from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_users import FastAPIUsers
from sqlalchemy.sql.functions import current_user

from auth.auth import auth_backend
from auth.database import User
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from connection_manager import ConnectionManager

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)
app = FastAPI(default_response_class=JSONResponse)
manager = ConnectionManager()

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)


@app.get("/user")
async def read_users_me(user: User = Depends(current_user)):
    return {"email": user.email}


async def get_manager():
    return manager


@app.websocket("/chat")
async def chat_websocket(websocket: WebSocket, chat_manager=Depends(get_manager)):
    await chat_manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await chat_manager.broadcast(message)
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket)


@app.get("/")
async def get():
    return HTMLResponse(open("templates/Chat.html").read())
