from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import os

# 枚举表示身份
class RoleEnum(int, Enum):
    student = 0
    teacher = 1

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件夹
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# 返回前端页面
@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open(os.path.join("frontend", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# 注册接口
@app.post("/api/register")
async def register(request: Request):
    data = await request.json()
    name = data.get("name", "")
    pwd = data.get("pass", "")
    role_str = data.get("role", "student")
    flag = RoleEnum[role_str].value if role_str in RoleEnum.__members__ else RoleEnum.student.value

    print(f"[REGISTER] name: {name}, pwd: {pwd}, flag: {flag}")
    return JSONResponse({"success": True, "message": "注册成功"})

# 登录接口
@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    name = data.get("name", "")
    pwd = data.get("pass", "")
    role_str = data.get("role", "student")
    flag = RoleEnum[role_str].value if role_str in RoleEnum.__members__ else RoleEnum.student.value

    print(f"[LOGIN] name: {name}, pwd: {pwd}, flag: {flag}")
    return JSONResponse({"success": True, "message": "登录成功"})

# 聊天接口
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("msg", "")
    print(f"[CHAT] msg: {msg}")
    return JSONResponse({"reply": "我不知道"})

