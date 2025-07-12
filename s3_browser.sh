#!/bin/bash

# ----------------------------------------
# s3_browser.sh
#
# 列出 S3 bucket 所有文件夹/文件
# 并可选择下载单个文件到 output_files 目录
#
# 用法：
#   ./s3_browser.sh
#
# ----------------------------------------

# ======== CONFIG ==========
ENDPOINT_URL="https://s3api-us-ks-2.runpod.io"
REGION="US-KS-2"
BUCKET="udn0m9qkz8"
PREFIX=""            # 从 bucket 根目录开始
TMP_LIST="s3_list.tmp"

# 配置 path-style
aws configure set default.s3.addressing_style path >/dev/null

# 清理临时文件
rm -f $TMP_LIST

# 创建下载目录
DOWNLOAD_DIR="./output_files"
mkdir -p "$DOWNLOAD_DIR"

# 递归遍历 S3
function list_s3_recursive() {
    local prefix="$1"

    aws s3api list-objects-v2 \
        --bucket "$BUCKET" \
        --prefix "$prefix" \
        --delimiter "/" \
        --endpoint-url "$ENDPOINT_URL" \
        --region "$REGION" \
        > s3api_result.json

    # 列出文件夹 (CommonPrefixes)
    folders=$(jq -r '.CommonPrefixes[].Prefix // empty' s3api_result.json)
    for folder in $folders; do
        echo "[DIR] $folder" | tee -a $TMP_LIST
        list_s3_recursive "$folder"
    done

    # 列出文件 (Contents)
    files=$(jq -r '.Contents[].Key // empty' s3api_result.json)
    for file in $files; do
        if [[ "$file" != */ ]]; then
            echo "$file" | tee -a $TMP_LIST
        fi
    done
}

# 开始遍历
echo "====== 正在列出 S3 bucket 所有文件 ======"
list_s3_recursive "$PREFIX"

echo
echo "以下是所有可下载的文件列表："
cat $TMP_LIST

echo
echo "请输入要下载的文件完整 Key（比如 SongGeneration/output/audios/sample_01_autoprompt.flac）"
read -rp "Key: " FILE_KEY

if [ -z "$FILE_KEY" ]; then
    echo "❌ 未输入 Key，退出。"
    exit 1
fi

LOCAL_NAME=$(basename "$FILE_KEY")
LOCAL_PATH="$DOWNLOAD_DIR/$LOCAL_NAME"

echo
echo "开始下载：$FILE_KEY → $LOCAL_PATH"

aws s3 cp \
    "s3://$BUCKET/$FILE_KEY" \
    "$LOCAL_PATH" \
    --endpoint-url "$ENDPOINT_URL" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ 下载成功：$LOCAL_PATH"
else
    echo "❌ 下载失败"
fi

# 清理
rm -f s3api_result.json $TMP_LIST