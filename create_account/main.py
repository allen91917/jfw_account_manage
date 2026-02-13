import os
import sys
import subprocess
import time
import platform
import random
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ============================
# 安全互動函數
# ============================
def safe_click(driver, element, retry=3):
    """安全點擊元素，支援重試和 JavaScript 備用方案"""
    for attempt in range(retry):
        try:
            # 先捲動到元素位置
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)
            time.sleep(0.3)
            
            # 等待元素可點擊
            WebDriverWait(driver, 5).until(lambda d: element.is_displayed() and element.is_enabled())
            
            # 嘗試正常點擊
            element.click()
            return True
        except Exception as e:
            if attempt < retry - 1:
                print(f"點擊失敗 (嘗試 {attempt + 1}/{retry})，使用 JavaScript 點擊...")
                try:
                    driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    time.sleep(0.5)
            else:
                print(f"點擊失敗：{e}")
                raise
    return False


def safe_send_keys(driver, element, text, retry=3):
    """安全輸入文字，支援重試"""
    for attempt in range(retry):
        try:
            # 先捲動到元素位置
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)
            time.sleep(0.3)
            
            # 等待元素可互動
            WebDriverWait(driver, 5).until(lambda d: element.is_displayed() and element.is_enabled())
            
            # 清空並輸入
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            if attempt < retry - 1:
                print(f"輸入失敗 (嘗試 {attempt + 1}/{retry})，重試中...")
                time.sleep(0.5)
            else:
                print(f"輸入失敗：{e}")
                raise
    return False


# ============================
# 建立 Chrome Driver(使用 ChromeDriverManager)
# ============================
def create_driver():
    """建立 Selenium ChromeDriver（使用 ChromeDriverManager 自動下載）"""

    # 直接使用 ChromeDriverManager 自動下載對應版本的 chromedriver
    print("使用 ChromeDriverManager 自動下載 chromedriver...")
    driver_path = ChromeDriverManager().install()

    # ============================
    # Chrome Options
    # ============================
    chrome_options = Options()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-save-password-bubble")

    # 關閉 Chrome 密碼儲存提示
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 設定視窗大小
    chrome_options.add_argument("--window-size=1280,800")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # ============================
    # 最強 anti-detection
    # ============================
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """
        },
    )

    return driver


# ============================
#  暱稱產生
# ============================

def generate_random_name():
    """隨機生成暱稱：可能單姓 or 雙姓 + 兩字名字"""

    # 單姓
    single_last_names = [
        "陳","林","黃","張","李","王","吳","劉","蔡","楊","許","鄭","謝","洪","郭",
        "邱","曾","廖","賴","徐","周","葉","蘇","莊","呂","江","何","蕭","羅","高",
        "潘","簡","朱","鍾","彭","游","翁","戴","范","宋","余","程","連","唐","馬",
        "董","石"
    ]

    # 新增：雙姓
    double_last_names = [
        "歐陽", "司馬", "諸葛", "上官", "司徒", "夏侯", "張簡", "范姜", "南宮", "西門",
        "東方", "皇甫", "慕容", "長孫", "宇文", "司空", "公孫", "令狐"
    ]

    # 讓雙姓比率稍微低一點（自然一點）
    if random.random() < 0.1:  # 10% 使用雙姓
        last_name = random.choice(double_last_names)
    else:
        last_name = random.choice(single_last_names)

    # 名字第一字
    first_char_list = [
        "家","冠","孟","志","承","柏","俊","冠","子","宇","怡","雅","淑","珮","品","欣",
        "嘉","彥","佳","宗","昇","美","詩","柔","芷","心","宥","睿","建","哲","廷","瑜",
        "郁","婉","雨","馨","明","偉","宏","諾","安","雲","語"
    ]
    
    # 名字第二字
    second_char_list = [
        "瑋","宇","軒","豪","翰","翰","宏","霖","傑","翔","叡","君","婷","芬","琪","萱",
        "婷","雯","萱","怡","蓉","慧","涵","婷","玲","琳","筑","芊","瑜","妤","平","晴",
        "哲","豪","明","偉","哲","成","達","潔","嫻","安","菲","菁"
    ]

    # 兩字名字組合
    name = last_name + random.choice(first_char_list) + random.choice(second_char_list)
    return name


# ============================
#  讀取用戶資訊
# ============================

def read_user_info():
    """從專案資料夾的用戶資訊.txt讀取帳號、密碼、創建數量"""
    # 取得專案資料夾路徑（支援打包後的 exe）
    if getattr(sys, 'frozen', False):
        # 打包後的 exe，使用 exe 所在目錄
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        # 開發環境，使用 .py 檔案所在目錄
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    info_file = os.path.join(BASE_DIR, "用戶資訊.txt")
    print(f"尋找用戶資訊檔案：{info_file}")
    
    if not os.path.exists(info_file):
        print(f"找不到檔案：{info_file}")
        print("請在專案資料夾建立 用戶資訊.txt，格式如下：")
        print("帳號,密碼,創建數量")
        print("user1,pass1,5")
        print("user2,pass2,10")
        return []
    
    users = []
    with open(info_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#") or i == 0:  # 跳過空行、註解和標題行
                continue
            
            parts = line.split(",")
            if len(parts) >= 3:
                account = parts[0].strip()
                password = parts[1].strip()
                try:
                    create_count = int(parts[2].strip())
                    if create_count <= 0:
                        print(f"警告：{account} 的創建數量 {create_count} 必須大於 0，跳過此帳號")
                        continue
                    users.append({
                        "account": account,
                        "password": password,
                        "create_count": create_count
                    })
                except ValueError:
                    print(f"警告：{account} 的創建數量格式錯誤，跳過此帳號")
    
    return users


# ============================
#  ⭐ 取得桌面路徑（支援 Windows 打包後的 exe）
# ============================

def get_desktop_path():
    """取得桌面路徑，支援 Windows/Mac，打包後也能正常運作"""
    try:
        # 方法 1：使用 os.path.expanduser (最常用)
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop):
            print(f"桌面路徑：{desktop}")
            return desktop
        
        # 方法 2：Windows 專用 - 使用環境變數
        if platform.system() == "Windows":
            userprofile = os.environ.get("USERPROFILE")
            if userprofile:
                desktop = os.path.join(userprofile, "Desktop")
                if os.path.exists(desktop):
                    print(f"桌面路徑：{desktop}")
                    return desktop
            
            # 方法 3：Windows - 中文桌面
            desktop = os.path.join(userprofile, "桌面")
            if os.path.exists(desktop):
                print(f"桌面路徑：{desktop}")
                return desktop
        
        # 方法 4：備用方案 - 使用當前執行檔所在目錄
        if getattr(sys, 'frozen', False):
            # 打包後的 exe
            exe_dir = os.path.dirname(sys.executable)
        else:
            # 開發環境
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"⚠️ 無法找到桌面，使用程式所在目錄：{exe_dir}")
        return exe_dir
        
    except Exception as e:
        print(f"❌ 獲取桌面路徑失敗：{e}")
        # 最終備用方案：當前目錄
        current_dir = os.getcwd()
        print(f"⚠️ 使用當前目錄：{current_dir}")
        return current_dir


# ============================
#  ⭐ 新增：帳號紀錄 TXT
# ============================

def init_agent_txt(agent_account, agent_password, txt_path):
    """第一次登入代理就建立 TXT 並寫入代理帳密（含中文標題）"""
    if not os.path.exists(txt_path):
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("代理帳號,代理密碼\n")
            f.write(f"{agent_account},{agent_password}\n")
            f.write("遊戲帳號,遊戲密碼\n")   # 先寫標題，內容等最後 append


def append_random_account(created_account, txt_path):
    """封控後把隨機生成的遊戲帳號寫入 TXT"""
    with open(txt_path, "a", encoding="utf-8") as f:
        f.write(f"{created_account['account']},{created_account['password']}\n")


# ============================
#  登入代理帳號
# ============================

def login(driver, account, password):
    """使用提供的帳號密碼自動登入，並導向個人頁面"""

    # print(f"[{account}] 準備登入...")

    # === 2️⃣ 定位 XPath ===
    account_xpath = "//input[@placeholder='請輸入帳號']"
    password_xpath = "//input[@placeholder='請輸入密碼']"
    login_button_xpath = "//button[contains(@class, 'login-btn')]"

    wait = WebDriverWait(driver, 15)

    try:
        # 等待頁面完全載入
        # print(f"[{account}] 等待登入頁面載入...")
        time.sleep(3)

        # === 3️⃣ 輸入帳號 ===
        print(f"[{account}] 尋找帳號輸入欄位...")
        acc_el = wait.until(EC.presence_of_element_located((By.XPATH, account_xpath)))
        safe_send_keys(driver, acc_el, account)
        # print(f"[{account}] ✔ 已輸入帳號")

        # === 4️⃣ 輸入密碼 ===
        pwd_el = wait.until(EC.presence_of_element_located((By.XPATH, password_xpath)))
        safe_send_keys(driver, pwd_el, password)
        # print(f"[{account}] ✔ 已輸入密碼")

        # print(f"[{account}] 帳密輸入完成！")

        # === 5️⃣ 點擊登入按鈕 ===
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, login_button_xpath)))
        safe_click(driver, login_btn)

        # 等待跳轉完成
        time.sleep(4) 

    except Exception as e:
        print(f"[{account}] 登入時發生錯誤：{e}")
        print(f"[{account}] 提示：請檢查網頁是否正常載入，或 XPath 是否已變更")


# ============================
#  代理控制 → 進入創帳號畫面
# ============================

def agent_control(driver, account, is_first_time=True):
    """登入完成後，依照順序點擊 代理控制 相關按鈕
    
    Args:
        driver: WebDriver 實例
        account: 帳號名稱
        is_first_time: 是否為第一次執行（第一次需要點擊帳號管理）
    """

    wait = WebDriverWait(driver, 15)

    if is_first_time:
        time.sleep(10)  # 第一次等待頁面加載
    else:
        time.sleep(2)  # 第二次開始只需短暫等待

    try:
        # === 1️⃣ 點擊「帳號管理」（只有第一次需要）===
        if is_first_time:
            account_manage_xpath = "//span[text()='帳號管理']"
            account_manage_btn = wait.until(EC.element_to_be_clickable((By.XPATH, account_manage_xpath)))
            account_manage_btn.click()
            # print(f"[{account}] ✔ 已點擊 帳號管理")
            time.sleep(3)  # 等待頁面加載
        
        # === 2️⃣ 點擊「代理帳號」 ===
        agent_button_xpath = "//span[text()='代理帳號']"
        agent_btn = wait.until(EC.element_to_be_clickable((By.XPATH, agent_button_xpath)))
        agent_btn.click()
        # print(f"[{account}] ✔ 已點擊 代理帳號")
        time.sleep(5)  # 等待頁面加載

        # === 3️⃣ 點擊「直屬玩家」 ===
        direct_member_xpath = "//div[text()='直屬玩家']"
        dm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, direct_member_xpath)))
        dm_btn.click()
        # print(f"[{account}] ✔ 已點擊 直屬玩家")
        time.sleep(2)  # 等待頁面加載

        # === 4️⃣ 點擊「創建信用/現金玩家」 ===
        create_button_xpath = "//span[contains(text(), '創建信用/現金玩家')]"
        create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, create_button_xpath)))
        create_btn.click()
        # print(f"[{account}] ✔ 已點擊 創建信用/現金玩家")
        time.sleep(2)  # 等待頁面加載

        # === 5️⃣ 點擊「創建現金玩家」 ===
        cash_member_xpath = "//div[text()='創建現金玩家']"
        cash_btn = wait.until(EC.element_to_be_clickable((By.XPATH, cash_member_xpath)))
        cash_btn.click()
        # print(f"[{account}] ✔ 已點擊 創建現金玩家")
        time.sleep(2)  # 等待頁面加載

        # === 6️⃣ 點擊「確認」 ===        
        confirm_button_xpath = "//span[text()=' 確認 ']"
        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))
        confirm_btn.click()
        # print(f"[{account}] ✔ 已點擊 確認")
        time.sleep(5)  # 等待頁面加載

    except Exception as e:
        print(f"[{account}] agent_control 發生錯誤：{e}")


# ============================
#  ✅ 這裡是你原本的 create_account（含下滑）
# ============================

def create_account(driver, account):
    """
    創建會員帳號流程（不使用 safe_click）
    1. 下滑到隨機按鈕
    2. 點擊隨機
    3. 讀取帳號
    4. 填寫密碼（aaaa1111）
    """

    wait = WebDriverWait(driver, 10)

    # 使用 input type 和順序來定位不同欄位
    # 帳號：第一個 type="text" 且 placeholder="請輸入" 的欄位
    account_input_xpath = "(//input[@type='text' and @placeholder='請輸入'])[1]"
    ok_button_xpath = "//button[contains(@class,'pk-button-ok')]"
    next1_button_xpath = "//button[contains(@class, 'el-button') and contains(., '下一步')]"

    # 密碼：第一個 type="password" 且 name="password" 的欄位
    password_input_xpath = "//input[@type='password' and @name='password']"
    # 確認密碼：第二個 type="password" 且 placeholder="請輸入" 的欄位（沒有 name 屬性）
    comfirm_password_input_xpath = "(//input[@type='password' and @placeholder='請輸入' and not(@name)])[1]"

    # ⭐ 固定密碼
    default_password = "Aaaa1111?"

    print(f"[{account}] 準備生成隨機帳號...")

    # === 0️⃣ 若有彈窗，先按 OK 關閉 ===
    try:
        ok_btn = driver.find_element(By.XPATH, ok_button_xpath)
        if ok_btn.is_displayed():
            print(f"[{account}] 偵測到彈窗 → 點擊 OK")
            safe_click(driver, ok_btn)
            time.sleep(0.5)
    except:
        pass

    # === 2️⃣ 點擊隨機開關 ===

    # 改用 switch 開關定位隨機功能
    random_switch_xpath = "//span[text()='隨機']"
    random_switch = wait.until(EC.element_to_be_clickable((By.XPATH, random_switch_xpath)))
    safe_click(driver, random_switch)
    # print(f"[{account}] 已點擊隨機開關")
    time.sleep(3)  # 等待帳號生成

    # === 3️⃣ 讀取生成帳號 ===
    account_input = wait.until(
        EC.presence_of_element_located((By.XPATH, account_input_xpath))
    )
    account_value = account_input.get_attribute("value")

    if not account_value:
        time.sleep(1)
        account_value = account_input.get_attribute("value")

    print(f"[{account}] 生成帳號：{account_value}")

    # === 4️⃣ 填入密碼 ===
    password_input = wait.until(
        EC.presence_of_element_located((By.XPATH, password_input_xpath))
    )
    safe_send_keys(driver, password_input, default_password)
    # print(f"[{account}] 已輸入密碼：{default_password}")

    comfirm_password_input = wait.until(
        EC.presence_of_element_located((By.XPATH, comfirm_password_input_xpath))
    )
    safe_send_keys(driver, comfirm_password_input, default_password)
    # print(f"[{account}] 已輸入確認密碼：{default_password}")

    # === 5️⃣ 填入暱稱 ===
    # 暱稱：第二個 type="text" 且 placeholder="請輸入" 的欄位
    nickname_xpath = "(//input[@type='text' and @placeholder='請輸入'])[2]"

    nickname_input = wait.until(
        EC.presence_of_element_located((By.XPATH, nickname_xpath))
    )

    nickname = generate_random_name()
    safe_send_keys(driver, nickname_input, nickname)

    print(f"[{account}] 已輸入暱稱：{nickname}")
    time.sleep(1)
    
    # === 6️⃣ 點擊下一步 === 
    next1_button = wait.until(EC.element_to_be_clickable((By.XPATH, next1_button_xpath)))
    safe_click(driver, next1_button)
    time.sleep(3)  # 等待下一頁加載

    # 若要回傳整組資訊，可以這樣：
    return {
        "account": account_value,
        "password": default_password
    }


# ============================
#  設定額度
# ============================

def set_credit_limit(driver, account):
    """設定額度為固定 5000，並按下下一步"""

    wait = WebDriverWait(driver, 10)

    # 額度輸入框：type="text" 的 input
    credit_input_xpath = "//input[@type='text' and contains(@class, 'el-input__inner')]"
    # 下一步按鈕：使用按鈕文字
    next2_button_xpath = "//button[contains(@class, 'el-button') and contains(., '下一步')]"

    limit_value = "5000"  # 固定額度

    print(f"[{account}] 開始設定額度為 5000 ...")

    # === 1️⃣ 找到額度輸入框 ===
    credit_input = wait.until(
        EC.presence_of_element_located((By.XPATH, credit_input_xpath))
    )

    # === 2️⃣ 輸入額度 ===
    safe_send_keys(driver, credit_input, limit_value)
    # print(f"[{account}] 已輸入額度：{limit_value}")

    time.sleep(0.3)

    # === 3️⃣ 按下下一步 ===
    next_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, next2_button_xpath))
    )
    safe_click(driver, next_button)

    # print(f"[{account}] 已按下下一步（Next）")
    time.sleep(3)  # 等待下一頁加載


# ============================
#  hold_position
# ============================

def hold_position(driver, account):
    """點擊下一步按鈕，然後下滑並點擊保存按鈕"""

    wait = WebDriverWait(driver, 10)

    # === 1️⃣ 往下滑動找到下一步按鈕 ===
    next_btn_xpath = "//button[contains(@class, 'el-button') and contains(., '下一步')]"
    next_btn = wait.until(EC.presence_of_element_located((By.XPATH, next_btn_xpath)))
    
    # 下滑到下一步按鈕
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
    # print(f"[{account}] 已下滑到下一步按鈕")
    time.sleep(1)
    
    # 點擊下一步
    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_btn_xpath)))
    safe_click(driver, next_btn)
    # print(f"[{account}] ✔ 已點擊下一步")
    time.sleep(2)

    # === 2️⃣ 找到保存按鈕並下滑 ===
    save_btn_xpath = "//div[contains(@class, 'save') and text()='保存']"
    save_btn = wait.until(EC.presence_of_element_located((By.XPATH, save_btn_xpath)))
    
    # 下滑到保存按鈕
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", save_btn)
    # print(f"[{account}] 已下滑到保存按鈕")
    time.sleep(2)

    # === 3️⃣ 點擊保存 ===
    save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, save_btn_xpath)))
    safe_click(driver, save_btn)
    # print(f"[{account}] ✔ 已點擊保存")
    time.sleep(2)


# ============================
#  risk_control
# ============================

def risk_control(driver, account):
    """
    封控（risk control）點擊下一步 → 點擊創建
    返回值：True 表示成功，False 表示失敗（不應寫入 txt）
    """

    wait = WebDriverWait(driver, 15)

    # print(f"[{account}] 進入封控流程...")
    
    try:
        # === 1️⃣ 點擊下一步 ===
        next_btn_xpath = "//button[contains(@class, 'el-button') and contains(., '下一步')]"
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_btn_xpath)))
        safe_click(driver, next_btn)
        # print(f"[{account}] ✔ 已點擊下一步")
        time.sleep(3)
        
        # === 2️⃣ 點擊創建(使用更精確的 XPath，避免點到創建會員)===
        create_btn_xpath = "//button[contains(@class, 'confirm-btn') and contains(., '創建')]"
        create_btn = wait.until(EC.element_to_be_clickable((By.XPATH, create_btn_xpath)))
        safe_click(driver, create_btn)
        # print(f"[{account}] ✔ 已點擊創建")
        time.sleep(5)
        
        # === 3️⃣ 導回主頁面防止 bug ===
        driver.get("https://ad.jfw-win.com/#/")
        # print(f"[{account}] ✔ 已導回主頁面")
        time.sleep(2)
        
        # === 4️⃣ 沒報錯就是成功 ===
        print(f"[{account}] ✔ 創建成功")
        return True
        
    except Exception as e:
        print(f"[{account}] ✗ 創建失敗: {e}")
        return False

# =======================================
#  單一用戶的工作流程
# =======================================

def process_user(user_info):
    """處理單一用戶的帳號創建流程"""
    account = user_info["account"]
    password = user_info["password"]
    create_count = user_info["create_count"]
    
    print(f"\n[{account}] ========== 開始處理 ==========")
    print(f"[{account}] 將創建 {create_count} 隻帳號")
    
    try:
        # 建立專屬的 driver
        driver = create_driver()
        
        # 前往登入頁面
        url = "https://ad.jfw-win.com/#/agent-login"
        print(f"[{account}] 前往網站：{url}")
        driver.get(url)
        
        # 登入
        login(driver, account, password)
        
        # 建立 TXT 檔案（使用穩健的桌面路徑獲取方法）
        desktop_path = get_desktop_path()
        txt_path = os.path.join(desktop_path, f"{account}.txt")
        print(f"[{account}]  TXT 檔案將儲存至：{txt_path}")
        init_agent_txt(account, password, txt_path)
        
        # 循環創建帳號
        for i in range(1, create_count + 1):
            print(f"\n[{account}] ===== 開始創建第 {i}/{create_count} 隻帳號 =====")
            
            # 第一次執行需要點擊「帳號管理」，第二次開始不需要
            is_first_time = (i == 1)
            agent_control(driver, account, is_first_time)
            created_account = create_account(driver, account)
            print(f"[{account}] 本次創建的帳號：{created_account}")
            
            set_credit_limit(driver, account)
            hold_position(driver, account)
            
            # 執行封控並檢查是否成功
            success = risk_control(driver, account)
            
            if success:
                # 只有成功才寫入 txt
                append_random_account(created_account, txt_path)
                print(f"[{account}] ✓ 已寫入：{created_account} → {txt_path}")
            else:
                # 失敗則不寫入，可能帳號已滿
                print(f"[{account}] ✗ 創建失敗（可能帳號已滿），本次帳號不寫入 txt")
                print(f"[{account}] 建議檢查代理帳號是否已達上限")
        
        print(f"\n[{account}] 全部 {create_count} 隻帳號創建完畢！")
        print(f"[{account}] 5 秒後關閉瀏覽器...")
        time.sleep(5)
        
        driver.quit()
        print(f"[{account}] ========== 處理完成 ==========\n")
        
    except Exception as e:
        print(f"[{account}] 發生錯誤：{e}")
        try:
            driver.quit()
        except:
            pass


# =======================================
#  主程式 - 使用多線程處理多個用戶
# =======================================

def main():
    print("=" * 50)
    print("自動創建帳號系統 (多線程版本)")
    print("=" * 50)
    
    # 讀取用戶資訊
    users = read_user_info()
    
    if not users:
        print("\n沒有找到有效的用戶資訊，程式結束。")
        return
    
    print(f"\n共找到 {len(users)} 個用戶：")
    for user in users:
        print(f"  - {user['account']} (創建 {user['create_count']} 個帳號)")
    
    # 分批處理參數
    BATCH_SIZE = 5  # 每批最多 5 個線程
    total_users = len(users)
    total_batches = (total_users + BATCH_SIZE - 1) // BATCH_SIZE  # 向上取整
    
    print(f"\n將分 {total_batches} 批處理，每批最多 {BATCH_SIZE} 個用戶")
    
    # 分批處理
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_users)
        batch_users = users[start_idx:end_idx]
        
        print(f"\n{'=' * 50}")
        print(f"開始處理第 {batch_num + 1}/{total_batches} 批 ({len(batch_users)} 個用戶)")
        print(f"{'=' * 50}")
        
        # 建立本批次的線程列表
        threads = []
        
        # 為本批次的每個用戶建立線程
        for user in batch_users:
            thread = threading.Thread(target=process_user, args=(user,))
            threads.append(thread)
            thread.start()
            time.sleep(2)  # 錯開啟動時間，避免同時啟動太多瀏覽器
        
        # 等待本批次所有線程完成
        for thread in threads:
            thread.join()
        
        print(f"\n第 {batch_num + 1}/{total_batches} 批處理完成！")
        
        # 如果還有下一批，稍作等待
        if batch_num < total_batches - 1:
            print(f"等待 3 秒後開始下一批...")
            time.sleep(3)
    
    print("\n" + "=" * 50)
    print("所有用戶處理完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
