from fastapi import Body, FastAPI, Request, HTTPException
import subprocess
# import hmac
# import hashlib
import logging
import os
import uvicorn
import sys
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import json

# 动态修改 sys.path，添加当前目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app.utils import verify_signature, run_command, prune_dangling_images

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 加载 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

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

# 全局日志配置
# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request: Request, exc: StarletteHTTPException):
#     logger.exception(f"HTTP error occurred: {exc.detail}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail},
#     )

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     logger.exception(f"Validation error occurred: {exc.errors()}")
#     return JSONResponse(
#         status_code=422,
#         content={"detail": exc.errors()},
#     )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"An error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
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

    payload_str = payload.decode('utf-8')
    
    try:
      payload_info = json.loads(payload_str)
    except Exception as e:
        logger.exception(f"json.loads failed(1): {str(e)}")
        payload_str = payload_str.replace('\\', '\\\\')
        try: 
          payload_info = json.loads(payload_str)
        except Exception as inner_e:
          logger.exception(f"json.loads failed(2): {str(inner_e)}")
          return { "message": "json.loads failed" }
    
    
    repository_info = payload_info["repository"]
    repository_name = repository_info["name"]
    logging.info(f"repository_name: {repository_name}")
    # 拉取最新代码并构建镜像
    repo_path = os.getenv("REPO_PATH", "REPO_PATH_empty")
    image_name = os.getenv("IMAGE_NAME", "IMAGE_NAME_empy")
    container_name = os.getenv("CONTAINER_NAME", "CONTAINER_NAME_empty")
    logging.info(f"repo_path:{repo_path}")
    logging.info(f"image_name: {image_name}")
    logging.info(f"container_name: {container_name}")

    docker_path = os.getenv("DOCKER_PATH", "./")
    # 1. 拿到docker_path之后，需要将它转换成绝对路径 docker_abs_path
    # 2. 如果路径不存在，创建路径；
    # 3. 如果路径存在，判断该路径下，是否有 repository_name 变量对应的目录，命名为 repository_abs_path
    # 4. repository_abs_path 目录， 存在：执行run_command(['git', 'pull'], cwd=repository_abs_path);
    # 不存在：执行run_command(['git', 'clone', repo_path]， cmd=docker_abs_path)
    docker_abs_path = os.path.abspath(docker_path)
    logger.info(f"docker_abs_path: {docker_abs_path}")
    if not os.path.exists(docker_abs_path):
       os.makedirs(docker_abs_path)
       logger.info(f"docker_abs_path: {docker_abs_path} not exist, created it!")
    
    repository_abs_path = os.path.join(docker_abs_path, repository_name)
    logger.info(f"repository_abs_path: {repository_abs_path}")
    if not os.path.exists(repository_abs_path):
        logger.info(f"repository_abs_path: {repository_abs_path} not exists!")
        try:
          run_command(['git', 'clone', repo_path], cwd=docker_abs_path)
        except Exception as e:
          logger.exception(f"Git clone failed: {str(e)}")
          return { "message": "Git clone failed" }
    else:
        logger.info(f"repository_abs_path: {repository_abs_path} exists!")
        try:
          run_command(['git', 'pull'], cwd=repository_abs_path)
        except Exception as e:
          logger.exception(f"Git pull failed: {str(e)}")
          return { "message": "Git pull failed" }

    try:
      logger.info(f"start docker build, image_name: {image_name}")
      # 这里构建成功后，之前的image_name会变成虚悬镜像
      run_command(['docker', 'build', '-t', image_name, '.'], cwd=repository_abs_path)
      logger.info(f"end docker build")
      # logger.info(f"start docker run, container_name:{container_name}, image_name: {image_name}")
      # run_command(['docker', 'run', '-d', '--name', container_name, '-p', '80:80', image_name])
      # logger.info(f"end docker run")
    except Exception as e:
      logging.error(f"An error occurred exec docker: {str(e)}")
      return { "message": "Docker command failed" }
    
    # 删除虚悬镜像
    try:
      prune_dangling_images()
    except Exception as e:
      logging.error(f"An error occurred prune_dangling_images: {str(e)}")
      return { "message": "prune_dangling_images() failed" }
    
    return {"message": "Success"}

@app.get("/")
async def root(request: Request):
    print('root_msg', os.getenv("GITHUB_SECRET", "your_secret_empty"))
    return { "message": "Read root path success" }

if __name__ == "__main__":
    uvicorn.run('app.main:app', host="0.0.0.0", port=9081, reload=True)
