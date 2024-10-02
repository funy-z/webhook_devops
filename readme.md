# 构建 Docker 镜像
docker build -t fastapi-webhook .

# 运行 Docker 容器
docker run -d --name fastapi-webhook -p 8000:8000 --env-file .env fastapi-webhook
