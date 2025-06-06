#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 设置变量
WORKFLOW_NAME="Alfred-Obsidian-Search"
TEMP_DIR="temp_workflow"
SRC_DIR="src"
OUTPUT_FILE="${WORKFLOW_NAME}.alfredworkflow"

# 清理函数
cleanup() {
    echo -e "${GREEN}Cleaning up...${NC}"
    rm -rf "$TEMP_DIR"
}

# 错误处理
set -e
trap cleanup EXIT

# 创建临时目录
echo -e "${GREEN}Creating temporary directory...${NC}"
mkdir -p "$TEMP_DIR"

# 复制文件
echo -e "${GREEN}Copying files...${NC}"
cp -r "$SRC_DIR"/* "$TEMP_DIR/"

# 创建 workflow 文件
echo -e "${GREEN}Creating workflow file...${NC}"
cd "$TEMP_DIR"
zip -r "../$OUTPUT_FILE" .
cd ..

echo -e "${GREEN}Workflow packaged successfully: $OUTPUT_FILE${NC}" 