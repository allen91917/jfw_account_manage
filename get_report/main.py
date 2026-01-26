import os
import sys
import platform
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

# ============================
# 取得執行檔所在目錄（支援 PyInstaller 打包）
# ============================
def get_base_dir():
    """
    取得程式執行的基礎目錄
    如果是 PyInstaller 打包的 exe，會返回 exe 所在目錄
    如果是 Python 腳本，會返回腳本所在目錄
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包後的 exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是 Python 腳本
        return os.path.dirname(os.path.abspath(__file__))

# ============================
# 設定參數（可獨立管理）
# ============================
LOGIN_URL = "https://ad.jfw-win.com/#/agent-login"
PERSONAL_URL = "https://ad.jfw-win.com/#/agent/report-manage/agentReport"

# ============================
# 報表功能 XPath 常數
# ============================
XPATH_REPORT = "//div[@class='link-item' and .//div[text()='報表']]"
XPATH_LEDGER = "//div[@class='pk-radio-label-normal' and text()='總帳損益']"
XPATH_LAST_WEEK = "//div[@class='pk-radio-label-mini' and text()='上週']"
XPATH_SEARCH = "/html/body/div/div[2]/div/section/main/div[4]/div[3]/button"

# ============================
# 建立 Selenium Driver
# ============================
def create_driver():
    """使用 webdriver-manager 自動管理 ChromeDriver"""
    print("正在初始化 Chrome Driver...")
    
    # Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 關閉密碼儲存提示和清除快取設定
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 清除快取相關設定
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--media-cache-size=0")

    # 使用 webdriver-manager 自動下載和管理 chromedriver
    try:
        driver_path = ChromeDriverManager().install()
        
        # macOS 需要移除 quarantine 屬性
        if platform.system() == 'Darwin':
            try:
                subprocess.run(['xattr', '-d', 'com.apple.quarantine', driver_path], 
                             capture_output=True, check=False)
                subprocess.run(['chmod', '+x', driver_path], 
                             capture_output=True, check=False)
                print("已處理 macOS ChromeDriver 權限")
            except Exception as e:
                print(f"權限處理警告: {e}")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 清除瀏覽器快取和 Cookies
        driver.execute_cdp_cmd('Network.clearBrowserCache', {})
        driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
        
        print("Chrome Driver 初始化完成")
        print("已清除快取和 Cookies")
        return driver
    except Exception as e:
        print(f"初始化 Chrome Driver 失敗: {e}")
        print("請確保已安裝 Google Chrome 瀏覽器")
        raise


# ============================
# 讀取用戶帳密 TXT
# ============================
def read_all_user_info():
    """
    讀取用戶資訊.txt 中的所有帳號密碼
    每一行格式： account,password
    回傳 List[Tuple[str, str]]
    """
    base_dir = get_base_dir()  # 使用新的函數取得正確路徑
    txt_path = os.path.join(base_dir, "用戶資訊.txt")

    if not os.path.exists(txt_path):
        print(f"找不到 用戶資訊.txt")
        print(f"當前查找路徑: {txt_path}")
        print(f"exe 所在目錄: {base_dir}")
        raise FileNotFoundError(f"找不到 用戶資訊.txt，請確保檔案與 exe 在同一資料夾")

    user_list = []
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "," not in line:
            print(f" 格式錯誤略過：{line}")
            continue

        account, password = line.split(",", 1)
        user_list.append((account.strip(), password.strip()))

    return user_list


def input_account_password(driver, account, password):
    """輸入指定帳密"""
    wait = WebDriverWait(driver, 10)

    acc_input = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//input[@placeholder='請輸入帳號']")
    ))
    acc_input.clear()
    acc_input.send_keys(account)

    pwd_input = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//input[@placeholder='請輸入密碼']")
    ))
    pwd_input.clear()
    pwd_input.send_keys(password)

    print(f" 已輸入帳密：{account} / {password}")



def click_login_button(driver):
    """
    自動點擊登入按鈕
    """
    wait = WebDriverWait(driver, 10)
    login_btn = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "button.login-btn.el-button"
    )))
    login_btn.click()
    # print("已點擊登入按鈕")

def click_radio_by_value(driver, value, timeout=10):
    """
    透過 radio 的 value 自動點擊 ElementUI 的 radio。
    
    :param driver: Selenium WebDriver
    :param value: <input value="xxx"> 的值，例如 "lastweek"
    :param timeout: 等待秒數
    """

    wait = WebDriverWait(driver, timeout)

    # 1. 找到 input[value=目標]
    input_el = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, f"input.el-radio__original[value='{value}']")
        )
    )

    # 2. 找到上層 label（ElementUI radio 結構固定）
    label_el = input_el.find_element(By.XPATH, "./ancestor::label")

    # 3. 如果已打勾，就不用點
    if "is-checked" in label_el.get_attribute("class"):
        # print(f"✔ Radio 已經被打勾：{value}")
        return

    # 4. 點擊 label（ElementUI 必須點 label 才會變 checked）
    driver.execute_script("arguments[0].click();", label_el)
    # print(f"👉 已幫你打勾：{value}")

def click_search_button(driver, timeout=10):
    """
    使用你提供的 XPath 點擊 <div class='reser'>立即查詢</div>
    """

    xpath = "//div[@class='reser' and text()='立即查詢']"

    wait = WebDriverWait(driver, timeout)

    # 等到元素可點擊
    btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

    # 使用 JS click 確保能點擊成功
    driver.execute_script("arguments[0].click();", btn)

    # print("XPath 已成功點擊:立即查詢")

def parse_agent_report(driver, week_type="上週"):
    """
    解析代理報表資料
    
    :param driver: Selenium WebDriver
    :param week_type: 報表週期，"本週" 或 "上週"
    """
    # 等待頁面載入完成
    time.sleep(3)
    
    # 取得頁面 HTML
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # 檢查是否有「無資料」圖片
    no_content_img = soup.find('img', {'src': lambda x: x and 'icon_no content' in x})
    if no_content_img:
        print(f"{week_type}無資料")
        return []
    
    # 找到所有的 strip-item
    strip_items = soup.find_all('div', {'class': 'strip-item', 'data-v-95d7a5b4': ''})
    
    results = []
    
    for item in strip_items:
        try:
            # 提取基本資訊
            data = {}
            
            # 報表週期
            data['報表週期'] = week_type
            
            # 帳號
            account_elem = item.find('div', {'class': 'cratedate'}, string=lambda x: x and '帳號' in x)
            if account_elem:
                data['帳號'] = account_elem.text.replace('帳號：', '').replace('帳號:', '').strip()
            
            # 名稱
            name_elem = item.find('div', {'class': 'cratedate'}, string=lambda x: x and '名稱' in x)
            if name_elem:
                data['名稱'] = name_elem.text.replace('名稱：', '').replace('名稱:', '').strip()
            
            # 狀態
            tag_elem = item.find('div', {'class': 'tag'})
            if tag_elem:
                txt_elem = tag_elem.find('div', {'class': 'txt'})
                if txt_elem:
                    data['狀態'] = txt_elem.text.strip()
            
            # 提取所有數據面板
            panels = item.find_all('div', {'class': 'panelBox'})
            
            for panel in panels:
                # 取得標題
                title_elem = panel.find('div', {'class': lambda x: x and 'item-data-feild-title' in x})
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # 取得數值
                value_elem = panel.find('div', {'class': 'item-data-des'})
                if value_elem:
                    # 處理數值,包含整數和小數部分
                    value_span = value_elem.find('span', recursive=False)
                    if value_span:
                        # 找到所有直接子 span
                        inner_spans = value_span.find_all('span', recursive=False)
                        if len(inner_spans) >= 2:
                            # 有整數和小數部分
                            integer_part = inner_spans[0].text.strip()
                            decimal_part = inner_spans[1].text.strip()
                            # 移除逗號
                            integer_part = integer_part.replace(',', '')
                            # 組合完整數值
                            value = integer_part + decimal_part
                        else:
                            # 只有一個值
                            value = value_span.text.strip().replace(',', '')
                    else:
                        # 沒有 span 標籤,直接取文字
                        value = value_elem.text.strip().replace(',', '')
                    
                    data[title] = value
            
            if data:
                results.append(data)
                
        except Exception as e:
            print(f"解析項目時發生錯誤: {e}")
            continue
    
    return results

def save_results_to_excel(all_results):
    """
    將所有結果儲存到 Excel 檔案,本週和上週分開工作表
    """
    # 取得桌面路徑
    desktop_path = Path.home() / "Desktop"
    
    # 產生檔案名稱
    filename = "代理報表.xlsx"
    filepath = desktop_path / filename
    
    # 分離本週和上週資料
    lastweek_data = [r for r in all_results if r.get('報表週期') == '上週']
    curweek_data = [r for r in all_results if r.get('報表週期') == '本週']
    
    # 轉換為 DataFrame
    df_last = pd.DataFrame(lastweek_data)
    df_cur = pd.DataFrame(curweek_data)
    
    # 移除報表週期欄位(因為已經用工作表名稱區分)
    if not df_last.empty:
        df_last = df_last.drop('報表週期', axis=1, errors='ignore')
    if not df_cur.empty:
        df_cur = df_cur.drop('報表週期', axis=1, errors='ignore')
    
    # 定義欄位順序
    column_order = [
        '帳號', '名稱', '狀態',
        '注單筆數', '下注金額', '有效投注',
        '玩家輸贏', '玩家退水', '玩家盈虧',
        '應收下線'
    ]
    
    # 調整上週資料欄位順序
    if not df_last.empty:
        existing_cols_last = [col for col in column_order if col in df_last.columns]
        df_last = df_last[existing_cols_last]
    
    # 調整本週資料欄位順序
    if not df_cur.empty:
        existing_cols_cur = [col for col in column_order if col in df_cur.columns]
        df_cur = df_cur[existing_cols_cur]
    
    # 將上週和本週資料合併到同一個 DataFrame
    # 在本週資料前加入空行分隔
    combined_data = []
    all_columns = []
    
    # 收集所有可能的欄位
    if not df_last.empty:
        all_columns = list(df_last.columns)
    if not df_cur.empty and not all_columns:
        all_columns = list(df_cur.columns)
    
    if not df_last.empty:
        # 加入上週標題行
        header_data = {col: '上週' if col == all_columns[0] else '' for col in all_columns}
        header_row = pd.DataFrame([header_data], columns=all_columns)
        combined_data.append(header_row)
        combined_data.append(df_last)
    
    if not df_cur.empty:
        # 加入空行和本週標題
        if combined_data:
            # 空行
            empty_data = {col: '' for col in all_columns}
            empty_row = pd.DataFrame([empty_data], columns=all_columns)
            combined_data.append(empty_row)
            # 再加一個空行
            combined_data.append(pd.DataFrame([empty_data], columns=all_columns))
        
        # 本週標題
        header_data = {col: '本週' if col == all_columns[0] else '' for col in all_columns}
        header_row = pd.DataFrame([header_data], columns=all_columns)
        combined_data.append(header_row)
        combined_data.append(df_cur)
    
    if combined_data:
        df_final = pd.concat(combined_data, ignore_index=True)
        
        # 加入上週和本週的應收下線總計
        if not df_last.empty and '應收下線' in df_last.columns:
            # 計算上週總計
            lastweek_total = pd.to_numeric(df_last['應收下線'], errors='coerce').sum()
            total_data_last = {col: '上週總計' if col == all_columns[0] else (f'{lastweek_total:.2f}' if col == '應收下線' else '') for col in all_columns}
            total_row_last = pd.DataFrame([total_data_last], columns=all_columns)
            
            # 找到上週資料的結束位置並插入總計行
            last_week_end_idx = len(df_last) + 1  # +1 因為有標題行
            df_final = pd.concat([
                df_final.iloc[:last_week_end_idx],
                total_row_last,
                df_final.iloc[last_week_end_idx:]
            ], ignore_index=True)
        
        if not df_cur.empty and '應收下線' in df_cur.columns:
            # 計算本週總計
            curweek_total = pd.to_numeric(df_cur['應收下線'], errors='coerce').sum()
            total_data_cur = {col: '本週總計' if col == all_columns[0] else (f'{curweek_total:.2f}' if col == '應收下線' else '') for col in all_columns}
            total_row_cur = pd.DataFrame([total_data_cur], columns=all_columns)
            
            # 在最後加入本週總計
            df_final = pd.concat([df_final, total_row_cur], ignore_index=True)
        
        # 儲存為單一工作表的 Excel
        df_final.to_excel(filepath, index=False, engine='openpyxl')
        
        print(f" Excel 已儲存至桌面: {filepath}")
        if not df_last.empty:
            print(f"上週資料: {len(df_last)} 筆")
            if '應收下線' in df_last.columns:
                lastweek_total = pd.to_numeric(df_last['應收下線'], errors='coerce').sum()
                print(f"上週應收下線總計: {lastweek_total:.2f}")
        if not df_cur.empty:
            print(f"本週資料: {len(df_cur)} 筆")
            if '應收下線' in df_cur.columns:
                curweek_total = pd.to_numeric(df_cur['應收下線'], errors='coerce').sum()
                print(f"本週應收下線總計: {curweek_total:.2f}")
    else:
        print("沒有資料可儲存")
        return None
    
    return str(filepath)

# ============================
# 主程式
# ============================
def main():
    user_list = read_all_user_info()
    all_results = []  # 儲存所有帳號的結果

    for index, (acc, pwd) in enumerate(user_list, start=1):
        print("\n============================")
        print(f"處理第 {index} 組帳號：{acc}")
        print("============================")

        driver = create_driver()
        driver.get(LOGIN_URL)

        input_account_password(driver, acc, pwd)
        time.sleep(1)
        click_login_button(driver)
        time.sleep(5)

        driver.get(PERSONAL_URL)
        time.sleep(5)
    
        
        # === 查詢上週報表 ===
        print("\n開始查詢【上週】報表...")
        click_radio_by_value(driver, "lastweek")
        time.sleep(2)
        click_search_button(driver)
        
        # 等待查詢結果載入
        print("等待查詢結果載入...")
        time.sleep(5)
        
        # 解析報表資料
        print("開始解析上週報表資料...")
        results_lastweek = parse_agent_report(driver, week_type="上週")
        
        if results_lastweek:
            print(f"成功解析上週 {len(results_lastweek)} 筆資料")
            all_results.extend(results_lastweek)
            
            # 顯示摘要
            print("\n上週資料摘要:")
            for idx, data in enumerate(results_lastweek[:3], 1):
                print(f"{idx}. {data.get('帳號', 'N/A')} - {data.get('名稱', 'N/A')}")
                if '玩家輸贏' in data:
                    print(f"玩家輸贏: {data['玩家輸贏']}")
            
            if len(results_lastweek) > 3:
                print(f"... 還有 {len(results_lastweek) - 3} 筆資料")
        else:
            print("上週未找到任何資料")
        
        # === 查詢本週報表 ===
        print("\n 開始查詢【本週】報表...")
        click_radio_by_value(driver, "curweek")
        time.sleep(2)
        click_search_button(driver)
        
        # 等待查詢結果載入
        print("等待查詢結果載入...")
        time.sleep(5)
        
        # 解析報表資料
        print("開始解析本週報表資料...")
        results_curweek = parse_agent_report(driver, week_type="本週")
        
        if results_curweek:
            print(f"成功解析本週 {len(results_curweek)} 筆資料")
            all_results.extend(results_curweek)
            
            # 顯示摘要
            print("\n本週資料摘要:")
            for idx, data in enumerate(results_curweek[:3], 1):
                print(f"{idx}. {data.get('帳號', 'N/A')} - {data.get('名稱', 'N/A')}")
                if '玩家輸贏' in data:
                    print(f"玩家輸贏: {data['玩家輸贏']}")
            
            if len(results_curweek) > 3:
                print(f"... 還有 {len(results_curweek) - 3} 筆資料")
        else:
            print("本週未找到任何資料")
        
        driver.quit()
        print(f"帳號 {acc} 處理完成")

    # 所有帳號處理完成後,統一儲存到一個 Excel
    if all_results:
        print("\n正在儲存所有資料...")
        save_results_to_excel(all_results)
    else:
        print("\n 沒有任何資料可儲存")

    print("\n 所有帳號流程已完成！")

if __name__ == "__main__":
    main()
