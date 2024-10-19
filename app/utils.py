import hmac
import hashlib
import os
import logging
import subprocess


def verify_signature(payload, signature):
    secret = os.getenv("GITHUB_SECRET", "your_secret_empty")
    logging.info(f"verify_signature secret:{secret}")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)


def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command, cwd=cwd, check=True, capture_output=True, text=True)
        logging.info(f"Command '{' '.join(command)}' executed successfully.")
        logging.info(f"stdout: {result.stdout}")
        logging.info(f"stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{' '.join(command)
                                  }' failed with return code {e.returncode}.")
        logging.error(f"stdout: {e.stdout}")
        logging.error(f"stderr: {e.stderr}")
        raise

# 清理虚悬镜像


def prune_dangling_images():
    try:
        # 执行 docker image prune -f 命令
        result = subprocess.run(['docker', 'image', 'prune', '-f'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)

        # 检查命令的退出状态
        if result.returncode == 0:
            logging.info("Successfully pruned dangling images.")
            logging.info(result.stdout)
        else:
            logging.error("Failed to prune dangling images.")
            logging.error(result.stderr)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise
