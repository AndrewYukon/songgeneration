#!/bin/bash

# ----------------------------------------
# s3_browser.sh
#
# Interactive S3 browser:
# - Navigate folders
# - Download individual files
# - Upload one or more files
#
# For S3-compatible services (e.g. RunPod)
#
# Usage:
#   ./s3_browser.sh
#
# ----------------------------------------

# ======== CONFIG ==========
ENDPOINT_URL="https://s3api-us-ks-2.runpod.io"
REGION="US-KS-2"
BUCKET="udn0m9qkz8"
PREFIX=""
DOWNLOAD_DIR="./output_files"

# Force path-style addressing
aws configure set default.s3.addressing_style path >/dev/null

mkdir -p "$DOWNLOAD_DIR"

function list_and_choose() {
    local current_prefix="$1"

    while true; do
        echo
        echo "⭐ Current path: s3://$BUCKET/$current_prefix"
        echo "------------------------------------------"

        rm -f s3api_result.json

        aws s3api list-objects-v2 \
            --bucket "$BUCKET" \
            --prefix "$current_prefix" \
            --delimiter "/" \
            --endpoint-url "$ENDPOINT_URL" \
            --region "$REGION" \
            > s3api_result.json

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

        OPTIONS+=("Go back to parent folder")
        OPTIONS+=("Upload file(s) to this folder")
        OPTIONS+=("Exit")

        if [ ${#OPTIONS[@]} -eq 3 ]; then
            echo "⚠️ This folder is empty."
        fi

        for i in "${!OPTIONS[@]}"; do
            printf "%3d) %s\n" $((i+1)) "${OPTIONS[$i]}"
        done

        read -rp "Enter the number of your choice: " choice

        if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
            echo "❌ Invalid input. Please enter a number."
            continue
        fi

        idx=$((choice-1))

        if [ $idx -lt 0 ] || [ $idx -ge ${#OPTIONS[@]} ]; then
            echo "❌ Input out of range."
            continue
        fi

        selection="${OPTIONS[$idx]}"

        case "$selection" in
            "Go back to parent folder")
                return 0
                ;;
            "Upload file(s) to this folder")
                upload_file "$current_prefix"
                ;;
            "Exit")
                echo "✅ Goodbye!"
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
    echo "🚀 Downloading s3://$BUCKET/$key → $DOWNLOAD_DIR/$filename"
    aws s3 cp \
        "s3://$BUCKET/$key" \
        "$DOWNLOAD_DIR/$filename" \
        --endpoint-url "$ENDPOINT_URL" \
        --region "$REGION"

    if [ $? -eq 0 ]; then
        echo "✅ Download complete: $DOWNLOAD_DIR/$filename"
    else
        echo "❌ Download failed."
    fi
}

function upload_file() {
    local target_prefix="$1"

    echo
    read -rp "Enter local file paths (separated by spaces): " local_files

    for local_file in $local_files; do
        if [ ! -f "$local_file" ]; then
            echo "❌ File does not exist: $local_file"
            continue
        fi

        file_name=$(basename "$local_file")
        s3_key="${target_prefix}${file_name}"

        # Check if file exists on S3
        echo "Checking if s3://$BUCKET/$s3_key exists..."
        aws s3api head-object \
            --bucket "$BUCKET" \
            --key "$s3_key" \
            --endpoint-url "$ENDPOINT_URL" \
            --region "$REGION" > head_object.json 2>/dev/null

        if [ $? -eq 0 ]; then
            existing_size=$(jq -r '.ContentLength' head_object.json)
            echo "⚠️ File already exists on S3: s3://$BUCKET/$s3_key"
            echo "Size on S3: $existing_size bytes"

            read -rp "Do you want to overwrite it? (y/n) " confirm
            if [[ "$confirm" != "y" ]]; then
                echo "🚫 Skipped upload: $local_file"
                rm -f head_object.json
                continue
            else
                echo "✅ Will overwrite the existing file."
            fi
        else
            echo "✅ No existing file on S3."
        fi

        rm -f head_object.json

        echo
        echo "🚀 Uploading $local_file → s3://$BUCKET/$s3_key"
        aws s3 cp \
            "$local_file" \
            "s3://$BUCKET/$s3_key" \
            --endpoint-url "$ENDPOINT_URL" \
            --region "$REGION"

        if [ $? -eq 0 ]; then
            echo "✅ Upload succeeded: s3://$BUCKET/$s3_key"

            local_size=$(stat -c %s "$local_file" 2>/dev/null || stat -f %z "$local_file")

            aws s3api head-object \
                --bucket "$BUCKET" \
                --key "$s3_key" \
                --endpoint-url "$ENDPOINT_URL" \
                --region "$REGION" > head_object.json

            s3_size=$(jq -r '.ContentLength' head_object.json)

            if [ "$local_size" == "$s3_size" ]; then
                echo "✅ File size verified: $local_size bytes"
            else
                echo "⚠️ Size mismatch!"
                echo "Local : $local_size bytes"
                echo "S3    : $s3_size bytes"
            fi
        else
            echo "❌ Upload failed: $local_file"
        fi

        rm -f head_object.json
        echo
    done

    echo "===== Current folder contents ====="
    list_current_folder "$target_prefix"
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
        echo "(This folder is empty)"
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

# Start browsing from the root of the bucket
list_and_choose "$PREFIX"