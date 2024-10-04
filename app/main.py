from fastapi import FastAPI, Request, HTTPException
import subprocess
# import hmac
# import hashlib
import logging
import os
import uvicorn
import sys
from fastapi.middleware.cors import CORSMiddleware
# 动态修改 sys.path，添加当前目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.utils import verify_signature

app = FastAPI()
# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('X-Hub-Signature-256')
    logging.info(f"webhook payload: {str(payload)}")
    logging.info(f"webhook signature: {signature}")
    if not verify_signature(payload, signature):
        logging.info(f"verify_signature no pass!")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # 拉取最新代码并构建镜像
    repo_path = os.getenv("REPO_PATH", "/path/to/your/repo")
    image_name = os.getenv("IMAGE_NAME", "your-image-name")
    container_name = os.getenv("CONTAINER_NAME", "your-container-name")
    logging.info(f"repo_path:{repo_path}")
    logging.info(f"image_name: {image_name}")
    logging.info(f"container_name: {container_name}")

    subprocess.run(['git', 'pull'], cwd=repo_path)
    subprocess.run(['docker', 'build', '-t', image_name, '.'], cwd=repo_path)
    subprocess.run(['docker', 'run', '-d', '--name', container_name, '-p', '80:80', image_name])
    
    return {"message": "Success"}

@app.get("/")
async def root(request: Request):
    return { "message": "Read root path success" }

if __name__ == "__main__":
    uvicorn.run('app.main:app', host="0.0.0.0", port=9081, reload=True)
