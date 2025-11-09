from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
import os
from src.db import SchoolDB
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

# ------------------- 数据库 -------------------
db = SchoolDB("school.db")

@app.on_event("startup")
async def startup_event():
    print("FastAPI 启动，执行初始化")
    # 这里调用你的 DB 初始化函数
    db.ensure_tables() # 假设你写了这个方法

# ------------------- 注册接口 -------------------
@app.post("/api/register")
async def register(request: Request):
    data = await request.json()
    name = data.get("name", "")
    pwd = data.get("pass", "")
    email = data.get("email", "")  # 前端需要传 email
    role_str = data.get("role", "student")
    flag = RoleEnum[role_str].value if role_str in RoleEnum.__members__ else RoleEnum.student.value

    try:
        if role_str == "student":
            user_id = db.register_student(name, pwd, email)
        else:
            user_id = db.register_teacher(name, pwd, email)
        print(f"[REGISTER] id: {user_id}, name: {name}, flag: {flag}")
        return JSONResponse({"success": True, "message": "注册成功", "id": user_id})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)})

# ------------------- 登录接口 -------------------
@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    name = data.get("name", "")
    pwd = data.get("pass", "")
    role_str = data.get("role", "student")
    flag = RoleEnum[role_str].value if role_str in RoleEnum.__members__ else RoleEnum.student.value

    if role_str == "student":
        ok = db.login_student(name, pwd)
    else:
        ok = db.login_teacher(name, pwd)

    if ok:
        print(f"[LOGIN] name: {name}, flag: {flag}")
        return JSONResponse({"success": True, "message": "登录成功"})
    else:
        return JSONResponse({"success": False, "message": "用户名或密码错误"})

# 聊天接口
@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("msg", "")
    print(f"[CHAT] msg: {msg}")
    return JSONResponse({"reply": "我不知道"})

