#!/bin/bash

# ----------------------------------------
# s3_browser.sh
#
# S3交互式多层浏览 + 下载脚本
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

        # 清理旧列表
        rm -f s3api_result.json

        # 列出当前目录
        aws s3api list-objects-v2 \
            --bucket "$BUCKET" \
            --prefix "$current_prefix" \
            --delimiter "/" \
            --endpoint-url "$ENDPOINT_URL" \
            --region "$REGION" \
            > s3api_result.json

        # 处理 folders
        folders=$(jq -r '.CommonPrefixes[].Prefix // empty' s3api_result.json)
        files=$(jq -r '.Contents[].Key // empty' s3api_result.json)

        OPTIONS=()

        if [[ -n "$folders" ]]; then
            while IFS= read -r folder; do
                # 去掉前缀部分，只显示相对路径
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

        # 添加退出选项
        OPTIONS+=("退出")

        # 如果空
        if [ ${#OPTIONS[@]} -eq 1 ]; then
            echo "⚠️ 该目录为空。"
            echo
            read -rp "输入 b 返回上层，或 q 退出: " input
            if [[ "$input" == "b" ]]; then
                return 0
            else
                echo "✅ 再见！"
                exit 0
            fi
        fi

        # 显示菜单
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

        if [[ "$selection" == "退出" ]]; then
            echo "✅ 再见！"
            exit 0
        elif [[ "$selection" == "[DIR]"* ]]; then
            dir_name=$(echo "$selection" | sed 's/^\[DIR\] //')
            new_prefix="$current_prefix$dir_name"
            list_and_choose "$new_prefix"
        else
            file_key="$current_prefix$selection"
            download_file "$file_key"
        fi
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

# 从 bucket 根目录开始
list_and_choose "$PREFIX"