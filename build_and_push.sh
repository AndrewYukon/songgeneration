#!/bin/bash

# --------------------------------------------
# 参数定义
# --------------------------------------------

IMAGE_NAME="linysh/songmix:pytorch2.6.0-py3.10-cuda12.4.1-runtime-ubuntu22.04-v1.4.5"
LOG_FILE="./build_and_push.log"

# --------------------------------------------
# 启动后台构建 + push
# --------------------------------------------

(
    echo "----------------------------------------"
    echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] Start building Docker image: $IMAGE_NAME"
    echo "----------------------------------------"

    docker build --no-cache -t "$IMAGE_NAME" ./docker-build

    if [ $? -eq 0 ]; then
        echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] Build completed successfully."
        echo "🚀 [$(date '+%Y-%m-%d %H:%M:%S')] Start pushing image to Docker Hub: $IMAGE_NAME"

        docker push "$IMAGE_NAME"

        if [ $? -eq 0 ]; then
            echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] Push completed successfully!"
        else
            echo "❌ [$(date '+%Y-%m-%d %H:%M:%S')] Push failed!"
            exit 2
        fi
    else
        echo "❌ [$(date '+%Y-%m-%d %H:%M:%S')] Build failed! Check logs above."
        exit 1
    fi
) &> "$LOG_FILE" &

echo "✅ Script started in background. Check progress with:"
echo "    tail -f $LOG_FILE"