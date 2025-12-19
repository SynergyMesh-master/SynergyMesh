#!/usr/bin/env python3
"""
工具模組 - Island Utilities

提供跨島嶼共用的輔助函數。
"""


class Colors:
    """終端機顏色輸出"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


def print_color(message: str, color: str) -> None:
    """輸出彩色訊息"""
    print(f"{color}{message}{Colors.NC}")


def print_info(message: str) -> None:
    """輸出資訊訊息"""
    print_color(f"[INFO] {message}", Colors.BLUE)


def print_success(message: str) -> None:
    """輸出成功訊息"""
    print_color(f"[SUCCESS] {message}", Colors.GREEN)


def print_warn(message: str) -> None:
    """輸出警告訊息"""
    print_color(f"[WARN] {message}", Colors.YELLOW)


def print_error(message: str) -> None:
    """輸出錯誤訊息"""
    print_color(f"[ERROR] {message}", Colors.RED)


__all__ = [
    "Colors",
    "print_color",
    "print_info",
    "print_success",
    "print_warn",
    "print_error",
]
