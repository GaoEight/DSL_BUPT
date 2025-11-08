from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def serve_index():
    # 直接读取当前目录下的 index.html
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    print("login:", data)
    return JSONResponse({"success": True, "message": "登录成功"})

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    print("chat:", data)
    return JSONResponse({"reply": "我不知道"})
