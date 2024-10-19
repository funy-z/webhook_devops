from utils import verify_signature
from ops_build import exec_build
from fastapi import Body, FastAPI, Request, HTTPException
import logging
import os
import uvicorn
import sys
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from concurrent.futures import ThreadPoolExecutor

import json

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 加载 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=2)

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
    # if not verify_signature(payload, signature):
    #     logging.info(f"verify_signature no pass!")
    #     raise HTTPException(status_code=403, detail="Forbidden")

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
            return {"message": "json.loads failed"}

    repository_info = payload_info["repository"]
    # 启动线程执行构建
    executor.submit(exec_build, repository_info)

    return {"message": "Success"}


@app.get("/")
async def root(request: Request):
    # logger(f'root_msg:{os.getenv("GITHUB_SECRET", "your_secret_empty")}')
    return {"message": "Read root path success"}

if __name__ == "__main__":
    uvicorn.run('app.main:app', host="0.0.0.0", port=9081, reload=True)
