#!/bin/bash
# 停止所有服务脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 日志配置
LOG_DIR="$SCRIPT_DIR/../logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/stop_services_${TIMESTAMP}.log"
LOG_LEVEL="INFO"  # 可选: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志级别映射
declare -A LOG_LEVEL_MAP
LOG_LEVEL_MAP["DEBUG"]=0
LOG_LEVEL_MAP["INFO"]=1
LOG_LEVEL_MAP["WARNING"]=2
LOG_LEVEL_MAP["ERROR"]=3
LOG_LEVEL_MAP["CRITICAL"]=4

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志级别转换函数
level_to_num() {
    echo "${LOG_LEVEL_MAP[$1]:-1}"
}

# 判断是否应该记录该级别的日志
should_log() {
    local log_level="$1"
    local current_level="$LOG_LEVEL"
    
    [ $(level_to_num "$log_level") -ge $(level_to_num "$current_level") ]
}

# 格式化日志信息
format_log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "[$timestamp] [$level] $message"
}

# 输出日志到控制台
log_to_console() {
    local level="$1"
    local message="$2"
    
    case "$level" in
        DEBUG)
            echo -e "${BLUE}$message${NC}"
            ;;
        INFO)
            echo -e "${GREEN}$message${NC}"
            ;;
        WARNING)
            echo -e "${YELLOW}$message${NC}"
            ;;
        ERROR|CRITICAL)
            echo -e "${RED}$message${NC}"
            ;;
    esac
}

# 通用日志函数
log() {
    local level="${1:-INFO}"
    local message="$2"
    
    if should_log "$level"; then
        local formatted_message=$(format_log "$level" "$message")
        
        # 输出到控制台
        log_to_console "$level" "$formatted_message"
        
        # 输出到文件
        echo "$formatted_message" >> "$LOG_FILE"
    fi
}

# 便捷日志函数
log_debug() {
    log "DEBUG" "$1"
}

log_info() {
    log "INFO" "$1"
}

log_warning() {
    log "WARNING" "$1"
}

log_error() {
    log "ERROR" "$1"
}

log_critical() {
    log "CRITICAL" "$1"
}

# 初始化日志
log_info "==========================================="
log_info "开始停止所有服务..."
log_info "日志文件: ${LOG_FILE}"
log_info "==========================================="

# 停止Infinity服务
log_info "停止Infinity嵌入服务..."
log_debug "执行脚本: $SCRIPT_DIR/stop_infinity_services.sh"
"$SCRIPT_DIR/stop_infinity_services.sh"
if [ $? -eq 0 ]; then
    log_info "Infinity服务停止成功"
else
    log_error "Infinity服务停止失败"
fi

# 停止Qdrant服务
log_info "停止Qdrant向量数据库服务..."
log_debug "执行脚本: $SCRIPT_DIR/stop_qdrant.sh"
"$SCRIPT_DIR/stop_qdrant.sh"
if [ $? -eq 0 ]; then
    log_info "Qdrant服务停止成功"
else
    log_error "Qdrant服务停止失败"
fi

log_info "==========================================="
log_info "所有服务停止操作完成！"
log_info "==========================================="
