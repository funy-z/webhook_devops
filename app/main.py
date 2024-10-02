from fastapi import FastAPI, Request, HTTPException
import subprocess
import hmac
import hashlib
import os
import uvicorn
from app.utils import verify_signature

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('X-Hub-Signature-256')
    
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # 拉取最新代码并构建镜像
    repo_path = os.getenv("REPO_PATH", "/path/to/your/repo")
    image_name = os.getenv("IMAGE_NAME", "your-image-name")
    container_name = os.getenv("CONTAINER_NAME", "your-container-name")
    
    subprocess.run(['git', 'pull'], cwd=repo_path)
    subprocess.run(['docker', 'build', '-t', image_name, '.'], cwd=repo_path)
    subprocess.run(['docker', 'run', '-d', '--name', container_name, '-p', '80:80', image_name])
    
    return {"message": "Success"}

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=9081)
