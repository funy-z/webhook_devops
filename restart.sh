# 停止容器服务
./stop.sh

# 删除latest镜像
docker image rm webhook_devops:latest

# 构建新镜像
./build_image.sh

# 重新启动docker-compose
./start.sh
