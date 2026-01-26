#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JFW_WIN PyInstaller 打包腳本
在 Windows 上執行此腳本來自動打包應用程式
"""

import os
import sys
import subprocess
import shutil

def print_header(text):
    """打印標題"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")

def print_step(step, total, text):
    """打印步驟"""
    print(f"[{step}/{total}] {text}...")

def run_command(command, description="執行命令"):
    """執行命令並處理錯誤"""
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[錯誤] {description}失敗")
        print(f"錯誤訊息: {e.stderr}")
        return False
    except Exception as e:
        print(f"\n[錯誤] {description}時發生異常: {e}")
        return False

def main():
    print_header("JFW_WIN 打包腳本")
    
    # 檢查 Python 版本
    if sys.version_info < (3, 7):
        print("[錯誤] 需要 Python 3.7 或更高版本")
        input("按 Enter 鍵退出...")
        sys.exit(1)
    
    print(f"✓ Python 版本: {sys.version.split()[0]}")
    
    # 步驟 1: 安裝 PyInstaller
    print_step(1, 4, "檢查並安裝 PyInstaller")
    if not run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"],
        "安裝 PyInstaller"
    ):
        input("按 Enter 鍵退出...")
        sys.exit(1)
    print("✓ PyInstaller 已就緒")
    
    # 步驟 2: 安裝依賴套件
    print_step(2, 4, "檢查並安裝依賴套件")
    packages = ["selenium", "webdriver-manager", "colorama"]
    for package in packages:
        if not run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", package],
            f"安裝 {package}"
        ):
            input("按 Enter 鍵退出...")
            sys.exit(1)
    print("✓ 依賴套件已安裝")
    
    # 步驟 3: 清理舊的建構檔案
    print_step(3, 4, "清理舊的建構檔案")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  ✓ 已刪除 {dir_name}/")
            except Exception as e:
                print(f"  ⚠ 無法刪除 {dir_name}/: {e}")
    print("✓ 清理完成")
    
    # 步驟 4: 執行打包
    print_step(4, 4, "開始打包 (這可能需要幾分鐘)")
    print()
    
    if not os.path.exists("JFW_WIN.spec"):
        print("[錯誤] 找不到 JFW_WIN.spec 檔案")
        input("按 Enter 鍵退出...")
        sys.exit(1)
    
    # 執行 PyInstaller (顯示輸出)
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "JFW_WIN.spec"],
        encoding='utf-8'
    )
    
    if result.returncode != 0:
        print_header("打包失敗")
        print("[錯誤] 打包過程中發生錯誤，請檢查上方訊息")
        input("按 Enter 鍵退出...")
        sys.exit(1)
    
    # 打包成功
    print_header("打包完成！")
    
    # 複製 用戶資訊.txt 到 dist 資料夾
    if os.path.exists("用戶資訊.txt"):
        try:
            shutil.copy2("用戶資訊.txt", "dist/用戶資訊.txt")
            print("✓ 已複製 用戶資訊.txt 到 dist 資料夾")
        except Exception as e:
            print(f"⚠ 複製 用戶資訊.txt 失敗: {e}")
    else:
        print("⚠ 找不到 用戶資訊.txt 檔案")
    
    print("\n✓ 可執行檔位置: dist/JFW_WIN.exe")
    print("✓ 帳號檔案位置: dist/用戶資訊.txt")
    print("\n提醒:")
    print("  • dist 資料夾中已包含所有需要的檔案")
    print("  • 首次執行時會自動下載 ChromeDriver")
    print()
    
    input("按 Enter 鍵退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[取消] 用戶中斷操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n[錯誤] 發生未預期的錯誤: {e}")
        input("按 Enter 鍵退出...")
        sys.exit(1)
