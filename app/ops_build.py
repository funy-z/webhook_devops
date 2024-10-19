import logging
import os

from utils import run_command, prune_dangling_images

logger = logging.getLogger('__main__')


def get_env_info(repository_name):
    if repository_name == 'ai_compoiso_backend':
        repo_path = os.getenv("REPO_PATH", "REPO_PATH_empty")
        image_name = os.getenv("IMAGE_NAME", "IMAGE_NAME_empy")
        container_name = os.getenv("CONTAINER_NAME", "CONTAINER_NAME_empty")
    # elif repository_name == 'ai-compoiso-frontend':
    else:
        repo_path = os.getenv("FRONTEND_REPO_PATH", "REPO_PATH_empty")
        image_name = os.getenv("FRONTEND_IMAGE_NAME", "IMAGE_NAME_empy")
        container_name = os.getenv(
            "FRONTEND_CONTAINER_NAME", "CONTAINER_NAME_empty")
    return {"repo_path": repo_path, "image_name": image_name, "container_name": container_name}


def exec_build(repository_info):
    repository_name = repository_info["name"]
    logger.info(f"repository_name: {repository_name}")
    # 拉取最新代码并构建镜像
    env_info = get_env_info(repository_name)
    repo_path = env_info["repo_path"]
    image_name = env_info["image_name"]
    container_name = env_info["container_name"]
    logger.info(f"repo_path:{repo_path}")
    logger.info(f"image_name: {image_name}")
    logger.info(f"container_name: {container_name}")

    docker_path = os.getenv("DOCKER_PATH", "./")
    docker_abs_path = os.path.abspath(docker_path)
    # 1. 拿到docker_path之后，需要将它转换成绝对路径 docker_abs_path
    # 2. 如果路径不存在，创建路径；
    # 3. 如果路径存在，判断该路径下，是否有 repository_name 变量对应的目录，命名为 repository_abs_path
    # 4. repository_abs_path 目录， 存在：执行run_command(['git', 'pull'], cwd=repository_abs_path);
    # 不存在：执行run_command(['git', 'clone', repo_path]， cmd=docker_abs_path)
    docker_abs_path = os.path.abspath(docker_path)
    logger.info(f"docker_abs_path: {docker_abs_path}")
    if not os.path.exists(docker_abs_path):
        os.makedirs(docker_abs_path)
        logger.info(f"docker_abs_path: "
                    f"{docker_abs_path} not exist, created it!")

    repository_abs_path = os.path.join(docker_abs_path, repository_name)
    logger.info(f"repository_abs_path: {repository_abs_path}")
    if not os.path.exists(repository_abs_path):
        logger.info(f"repository_abs_path: {repository_abs_path} not exists!")
        try:
            run_command(['git', 'clone', repo_path], cwd=docker_abs_path)
        except Exception as e:
            logger.exception(f"Git clone failed: {str(e)}")
            return {"message": "Git clone failed"}
    else:
        logger.info(f"repository_abs_path: {repository_abs_path} exists!")
        try:
            run_command(['git', 'pull'], cwd=repository_abs_path)
        except Exception as e:
            logger.exception(f"Git pull failed: {str(e)}")
            return {"message": "Git pull failed"}

    try:
        logger.info(f"start docker build, image_name: {image_name}")
        # 这里构建成功后，之前的image_name会变成虚悬镜像
        run_command(['docker', 'build', '-t', image_name, '.'],
                    cwd=repository_abs_path)
        logger.info(f"end docker build")
    except Exception as e:
        logging.error(f"An error occurred exec docker: {str(e)}")
        return {"message": "Docker command failed"}

    # 删除虚悬镜像
    try:
        prune_dangling_images()
    except Exception as e:
        logging.error(f"An error occurred prune_dangling_images: {str(e)}")
        return {"message": "prune_dangling_images() failed"}

    # 更新docker-compose中的ai-composiso-backend
    try:
        # docker-compose -f docker-compose.yml up -d --no-deps ai-composiso-backend
        logger.info(
            f"update docker-compose, container_name:{container_name}, image_name: {image_name}")
        run_command(['docker-compose', '-f', '/app/docker-compose.yml', 'up',
                     '-d', '--no-deps', 'ai-composiso-backend'])
        logger.info(f"end update docker-compose")
    except Exception as e:
        logging.error(f"An error occurred update docker-compose: {str(e)}")
        return {"message": "Update docker-compose failed"}
