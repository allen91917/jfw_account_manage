# -*- coding: utf-8 -*-
"""
Build script for creating Windows executable
確保在 Windows 環境下執行此腳本
"""

import os
import sys
import shutil
import subprocess

def build_exe():
    """使用 PyInstaller 打包成 exe"""
    
    print("=" * 60)
    print("🚀 開始打包 create_account.py 成 exe")
    print("=" * 60)
    
    # 確認是否在 Windows 環境
    if sys.platform != "win32":
        print("⚠️  警告：此腳本建議在 Windows 環境下執行")
        response = input("是否繼續？(y/n): ").strip().lower()
        if response != 'y':
            print("❌ 取消打包")
            return
    
    # 檢查 PyInstaller 是否安裝
    try:
        import PyInstaller
        print("✅ PyInstaller 已安裝")
    except ImportError:
        print("❌ PyInstaller 未安裝，正在安裝...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 安裝完成")
    
    # 清理舊的 build 和 dist 資料夾
    if os.path.exists("build"):
        print("🗑️  清理舊的 build 資料夾...")
        shutil.rmtree("build")
    
    if os.path.exists("dist"):
        print("🗑️  清理舊的 dist 資料夾...")
        shutil.rmtree("dist")
    
    # PyInstaller 指令
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包成單一 exe
        "--windowed",                   # 不顯示 console (如果需要看 console，移除此行)
        "--name=CreateAccount",         # exe 名稱
        "--clean",                      # 清理暫存檔
        "--noupx",                      # 不使用 UPX 壓縮（避免部分防毒軟體誤判）
        "create_account.py"
    ]
    
    # 如果需要顯示 console（方便看輸出），改用這個 cmd
    cmd_with_console = [
        "pyinstaller",
        "--onefile",                    # 打包成單一 exe
        "--console",                    # 顯示 console 視窗
        "--name=CreateAccount",         # exe 名稱
        "--clean",                      # 清理暫存檔
        "--noupx",                      # 不使用 UPX 壓縮
        "create_account.py"
    ]
    
    print("\n📦 開始打包...")
    print("⚙️  執行指令：", " ".join(cmd_with_console))
    print()
    
    # 執行打包（使用有 console 的版本）
    result = subprocess.run(cmd_with_console, shell=True)
    
    if result.returncode != 0:
        print("\n❌ 打包失敗！")
        return
    
    print("\n✅ 打包成功！")
    
    # 檢查 dist 資料夾
    if not os.path.exists("dist"):
        print("❌ dist 資料夾不存在")
        return
    
    # 建立說明檔
    readme_content = """
=================================
CreateAccount 使用說明
=================================

📁 檔案說明：
- CreateAccount.exe: 主程式

💡 使用方式：
1. 直接執行 CreateAccount.exe
2. 依照提示輸入帳號密碼
3. 選擇要創建 5 隻或 10 隻帳號
4. 程式會自動在桌面產生 txt 檔案記錄帳號資訊

⚠️  注意事項：
- 確保系統已安裝 Google Chrome 瀏覽器
- 程式會自動下載對應版本的 ChromeDriver
- 程式會自動處理中文路徑
- 生成的 txt 檔案會儲存在桌面
- 首次執行可能需要較長時間下載 ChromeDriver

🔧 系統需求：
- Windows 7/10/11
- Google Chrome 瀏覽器
- 網路連線（首次執行需下載 ChromeDriver）

=================================
"""
    
    readme_path = os.path.join("dist", "使用說明.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"📝 已建立使用說明檔：{readme_path}")
    
    # 清理 spec 檔
    spec_file = "CreateAccount.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"🗑️  已清理 {spec_file}")
    
    print("\n" + "=" * 60)
    print("🎉 打包完成！")
    print("=" * 60)
    print(f"📂 檔案位置：{os.path.abspath('dist')}")
    print("\n📦 dist 資料夾內容：")
    for item in os.listdir("dist"):
        print(f"   - {item}")
    print("\n✨ 可以將整個 dist 資料夾複製到其他 Windows 電腦使用")
    print("=" * 60)


def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("🛠️  CreateAccount 打包工具")
    print("=" * 60)
    print("\n此工具會將 create_account.py 打包成 Windows exe 檔案")
    print("\n打包選項：")
    print("  1. 包含 console 視窗（可看到執行過程，建議）")
    print("  2. 不含 console 視窗（純 GUI 模式）")
    print()
    
    choice = input("請選擇打包選項 (1/2) [預設:1]: ").strip()
    
    if choice == "2":
        print("\n⚠️  注意：選擇選項 2 將無法看到程式執行過程")
        confirm = input("確定繼續？(y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 取消打包")
            return
    
    build_exe()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷")
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按 Enter 鍵結束...")
