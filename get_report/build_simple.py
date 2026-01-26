#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡易打包腳本 - 一鍵打包成 exe
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 設定
EXE_NAME = "JFW資訊抓取工具"
MAIN_SCRIPT = "main.py"

def main():
    base_dir = Path(__file__).parent
    
    print("🚀 開始打包...")
    
    # 1. 清理舊檔案
    print("\n🧹 清理舊檔案...")
    for folder in ["build", "dist", "__pycache__"]:
        if (base_dir / folder).exists():
            shutil.rmtree(base_dir / folder)
            print(f"  ✔ 已刪除 {folder}/")
    
    for file in [f"{EXE_NAME}.spec"]:
        if (base_dir / file).exists():
            (base_dir / file).unlink()
            print(f"  ✔ 已刪除 {file}")
    
    # 2. 執行 PyInstaller
    print("\n📦 執行 PyInstaller...")
    cmd = [
        "pyinstaller",
        "--onefile",                    # 單一檔案
        "--clean",                      # 清理暫存
        "--noconfirm",                  # 不詢問
        f"--name={EXE_NAME}",           # exe 名稱
        "--hidden-import=selenium",     # 隱藏導入
        "--hidden-import=bs4",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=webdriver_manager",
        "--collect-all=webdriver_manager",  # 包含所有 webdriver-manager 資源
        MAIN_SCRIPT
    ]
    
    result = subprocess.run(cmd, cwd=str(base_dir))
    
    if result.returncode != 0:
        print("\n❌ 打包失敗！")
        sys.exit(1)
    
    # 3. 複製必要檔案到 dist
    print("\n📋 複製檔案...")
    dist_dir = base_dir / "dist"
    for file in ["用戶資訊.txt", "說明.md"]:
        if (base_dir / file).exists():
            shutil.copy2(base_dir / file, dist_dir / file)
            print(f"  ✔ {file}")
    
    # 4. 清理暫存檔案
    print("\n🧹 清理暫存檔案...")
    if (base_dir / "build").exists():
        shutil.rmtree(base_dir / "build")
        print("  ✔ 已刪除 build/")
    
    if (base_dir / f"{EXE_NAME}.spec").exists():
        (base_dir / f"{EXE_NAME}.spec").unlink()
        print("  ✔ 已刪除 .spec 檔")
    
    # 5. 完成
    print("\n" + "=" * 50)
    print("🎉 打包完成！")
    print("=" * 50)
    print(f"\n📦 輸出位置: {dist_dir}")
    
    print("\n📝 dist 資料夾內容:")
    if dist_dir.exists():
        for item in sorted(dist_dir.iterdir()):
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"  • {item.name} ({size_mb:.2f} MB)")
            else:
                print(f"  • {item.name}/")
    
    print("\n" + "=" * 50)
    print("📋 使用說明:")
    print("=" * 50)
    print("1. ✅ 使用 webdriver-manager，無需手動放置 chromedriver")
    print("2. 💡 程式會自動下載對應的 ChromeDriver 版本")
    print("3. 📝 請確保「用戶資訊.txt」與執行檔在同一目錄")
    print("4. 📊 報表會自動儲存到桌面: 代理報表.xlsx")
    print("5. 🌐 需要網路連線來下載 ChromeDriver")

if __name__ == "__main__":
    main()
