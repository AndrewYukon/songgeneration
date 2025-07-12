#!/bin/bash

# ----------------------------------------
# s3_browser.sh
#
# S3交互式多层浏览 + 下载 + 上传脚本
#
# 用法：
#   ./s3_browser.sh
#
# ----------------------------------------

# ======== CONFIG ==========
ENDPOINT_URL="https://s3api-us-ks-2.runpod.io"
REGION="US-KS-2"
BUCKET="udn0m9qkz8"
PREFIX=""
DOWNLOAD_DIR="./output_files"

# 配置 path-style
aws configure set default.s3.addressing_style path >/dev/null

mkdir -p "$DOWNLOAD_DIR"

function list_and_choose() {
    local current_prefix="$1"

    while true; do
        echo
        echo "⭐ 当前路径：s3://$BUCKET/$current_prefix"
        echo "------------------------------------------"

        rm -f s3api_result.json

        # 列出当前目录
        aws s3api list-objects-v2 \
            --bucket "$BUCKET" \
            --prefix "$current_prefix" \
            --delimiter "/" \
            --endpoint-url "$ENDPOINT_URL" \
            --region "$REGION" \
            > s3api_result.json

        # 修正 jq null 报错
        folders=$(jq -r '.CommonPrefixes? // [] | .[].Prefix' s3api_result.json)
        files=$(jq -r '.Contents? // [] | .[].Key' s3api_result.json)

        OPTIONS=()

        if [[ -n "$folders" ]]; then
            while IFS= read -r folder; do
                display_name=${folder#"$current_prefix"}
                OPTIONS+=("[DIR] $display_name")
            done <<< "$folders"
        fi

        if [[ -n "$files" ]]; then
            while IFS= read -r file; do
                if [[ "$file" != */ ]]; then
                    display_name=${file#"$current_prefix"}
                    OPTIONS+=("$display_name")
                fi
            done <<< "$files"
        fi

        OPTIONS+=("返回上层")
        OPTIONS+=("上传文件到此目录")
        OPTIONS+=("退出")

        if [ ${#OPTIONS[@]} -eq 3 ]; then
            echo "⚠️ 该目录为空。"
        fi

        for i in "${!OPTIONS[@]}"; do
            printf "%3d) %s\n" $((i+1)) "${OPTIONS[$i]}"
        done

        read -rp "请输入序号选择: " choice

        if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
            echo "❌ 非法输入，必须输入数字。"
            continue
        fi

        idx=$((choice-1))

        if [ $idx -lt 0 ] || [ $idx -ge ${#OPTIONS[@]} ]; then
            echo "❌ 输入超出范围。"
            continue
        fi

        selection="${OPTIONS[$idx]}"

        case "$selection" in
            "返回上层")
                return 0
                ;;
            "上传文件到此目录")
                upload_file "$current_prefix"
                ;;
            "退出")
                echo "✅ 再见！"
                exit 0
                ;;
            *)
                if [[ "$selection" == "[DIR]"* ]]; then
                    dir_name=$(echo "$selection" | sed 's/^\[DIR\] //')
                    new_prefix="$current_prefix$dir_name"
                    list_and_choose "$new_prefix"
                else
                    file_key="$current_prefix$selection"
                    download_file "$file_key"
                fi
                ;;
        esac
    done
}

function download_file() {
    local key="$1"
    local filename=$(basename "$key")

    echo
    echo "🚀 开始下载 s3://$BUCKET/$key → $DOWNLOAD_DIR/$filename"
    aws s3 cp \
        "s3://$BUCKET/$key" \
        "$DOWNLOAD_DIR/$filename" \
        --endpoint-url "$ENDPOINT_URL" \
        --region "$REGION"

    if [ $? -eq 0 ]; then
        echo "✅ 下载完成：$DOWNLOAD_DIR/$filename"
    else
        echo "❌ 下载失败。"
    fi
}

function upload_file() {
    local target_prefix="$1"

    echo
    read -rp "请输入本地文件路径（例如 /path/to/file.txt）: " local_file

    if [ ! -f "$local_file" ]; then
        echo "❌ 文件不存在: $local_file"
        return
    fi

    file_name=$(basename "$local_file")
    s3_key="${target_prefix}${file_name}"

    # 检查 S3 是否已存在此文件
    echo "正在检查是否存在 s3://$BUCKET/$s3_key ..."
    aws s3api head-object \
        --bucket "$BUCKET" \
        --key "$s3_key" \
        --endpoint-url "$ENDPOINT_URL" \
        --region "$REGION" > head_object.json 2>/dev/null

    if [ $? -eq 0 ]; then
        # 文件已存在
        existing_size=$(jq -r '.ContentLength' head_object.json)
        echo "⚠️ 目标 S3 中已存在同名文件：s3://$BUCKET/$s3_key"
        echo "大小：$existing_size bytes"

        read -rp "是否覆盖？(y/n) " confirm
        if [[ "$confirm" != "y" ]]; then
            echo "🚫 跳过上传：$local_file"
            rm -f head_object.json
            return
        else
            echo "✅ 将覆盖原文件。"
        fi
    else
        echo "✅ 目标 S3 中不存在同名文件。"
    fi

    rm -f head_object.json

    echo
    echo "🚀 开始上传 $local_file → s3://$BUCKET/$s3_key"
    aws s3 cp \
        "$local_file" \
        "s3://$BUCKET/$s3_key" \
        --endpoint-url "$ENDPOINT_URL" \
        --region "$REGION"

    if [ $? -eq 0 ]; then
        echo "✅ 上传成功：s3://$BUCKET/$s3_key"

        # 验证文件大小
        local_size=$(stat -c %s "$local_file" 2>/dev/null || stat -f %z "$local_file")

        aws s3api head-object \
            --bucket "$BUCKET" \
            --key "$s3_key" \
            --endpoint-url "$ENDPOINT_URL" \
            --region "$REGION" > head_object.json

        s3_size=$(jq -r '.ContentLength' head_object.json)

        if [ "$local_size" == "$s3_size" ]; then
            echo "✅ 文件大小一致：$local_size bytes"
        else
            echo "⚠️ 文件大小不一致！"
            echo "本地：$local_size bytes"
            echo "S3  ：$s3_size bytes"
        fi

        echo
        echo "===== 当前目录最新内容 ====="
        list_current_folder "$target_prefix"
    else
        echo "❌ 上传失败。"
    fi

    rm -f head_object.json
}

function list_current_folder() {
    local prefix="$1"

    aws s3api list-objects-v2 \
        --bucket "$BUCKET" \
        --prefix "$prefix" \
        --delimiter "/" \
        --endpoint-url "$ENDPOINT_URL" \
        --region "$REGION" \
        > s3api_result.json

    folders=$(jq -r '.CommonPrefixes? // [] | .[].Prefix' s3api_result.json)
    files=$(jq -r '.Contents? // [] | .[].Key' s3api_result.json)

    if [[ -z "$folders" && -z "$files" ]]; then
        echo "(该目录为空)"
        return
    fi

    for folder in $folders; do
        display_name=${folder#"$prefix"}
        echo "[DIR] $display_name"
    done

    for file in $files; do
        if [[ "$file" != */ ]]; then
            display_name=${file#"$prefix"}
            echo "$display_name"
        fi
    done
}

# 从 bucket 根目录开始
list_and_choose "$PREFIX"