import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from colorama import init, Fore, Style
from datetime import datetime
import subprocess
import logging
from webdriver_manager.chrome import ChromeDriverManager
import re
from selenium.common.exceptions import StaleElementReferenceException
import threading


def get_base_dir():
    """获取资源根目录"""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        _internal_dir = os.path.join(base_dir, '_internal')
        if os.path.exists(_internal_dir):
            return _internal_dir
        return base_dir
    else:
        return os.path.dirname(os.path.abspath(__file__))


base_dir = get_base_dir()

# 建立執行緒鎖,避免日誌輸出混亂
print_lock = threading.Lock()


def load_accounts():
    """加载账号信息 (账号, 密码, 调整金额)"""
    accounts = []
    invalid_entries = []
    accounts_file = os.path.join(base_dir, "用戶資訊.txt")
    pattern = re.compile(r"^[A-Za-z0-9]+$")

    try:
        with open(accounts_file, 'r', encoding='utf-8-sig') as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line or line.lstrip().startswith(('#', '＃')):
                    continue

                parts = line.replace('，', ',').split(',')

                if len(parts) == 3:
                    account, password, amount = map(str.strip, parts)
                    valid = True
                    if not pattern.match(account):
                        invalid_entries.append(f"\033[31m第 {line_number} 行 - 無效帳號: {account}\033[0m")
                        valid = False
                    if not pattern.match(password):
                        invalid_entries.append(f"\033[31m第 {line_number} 行 - 無效密碼: {password}\033[0m")
                        valid = False
                    if not amount.isdigit():
                        invalid_entries.append(f"\033[31m第 {line_number} 行 - 無效金額: {amount}\033[0m")
                        valid = False
                    if valid:
                        accounts.append((account, password, int(amount)))
                else:
                    invalid_entries.append(
                        f"\033[31m第 {line_number} 行 - 格式錯誤，應為「帳號,密碼,調整金額」: {line}\033[0m"
                    )

    except Exception as e:
        print(f"\033[31m錯誤：讀取帳號文件失敗：{e}\033[0m")
        sys.exit(1)

    if invalid_entries:
        print("\033[33m========================================\033[0m")
        print("\n".join(invalid_entries))
        print("\033[33m========================================\033[0m")
        print("\n\033[33m請修改格式錯誤後重新執行腳本。\033[0m\n")
        input("按 Enter 結束...")
        sys.exit(1)
    else:
        print("\033[33m========================================\033[0m")
        print("\033[33m所有帳號格式均正確\033[0m")
        print(f"\033[32m共讀取到 {len(accounts)} 組帳號\033[0m")
        print("\033[33m========================================\033[0m\n")
    
    return accounts


def init_environment():
    """初始化環境設定"""
    logging.basicConfig(level=logging.ERROR)
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    sys.stdout.reconfigure(encoding='utf-8')
    os.system("title " + "RICH_PANDA後台管理系統")
    os.system("mode con: cols=100 lines=30")

    try:
        result = subprocess.run(["chromedriver", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            version = result.stdout.split()[1]
            print(f"ChromeDriver {version}")
        else:
            print("ChromeDriver 將自動下載安裝")
    except (FileNotFoundError, Exception) as e:
        print("ChromeDriver 未安裝，將使用 webdriver-manager 自動下載")

    init(autoreset=True)


def init_driver():
    """初始化 Chrome WebDriver"""
    try:
        with print_lock:
            print("\n正在初始化 Chrome 瀏覽器...")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--log-level=3')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(service=service, options=options)
        with print_lock:
            print("Chrome 瀏覽器初始化成功！\n")
        return driver
    except Exception as e:
        with print_lock:
            print(f"\033[31m錯誤：無法啟動 Chrome 瀏覽器：{e}\033[0m")
            print("\033[33m請確保已安裝 Google Chrome 瀏覽器\033[0m")
            print("\033[33m下載地址：https://www.google.com/chrome/\033[0m")
        input("\n按 Enter 結束...")
        sys.exit(1)


def click_with_retry(driver, xpath, next_xpath, retries=3, delay=1):
    """尝试点击元素，如果下一个元素未出现则重试"""
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            time.sleep(0.5)
            element.click()
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, next_xpath)))
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"点击失败：{xpath}，错误信息：{e}")
                return False


def wait_for_scroll_end(driver, timeout=10, interval=0.1):
    """等待滚动结束"""
    end_time = time.time() + timeout
    last_scroll_position = driver.execute_script("return window.pageYOffset;")
    while time.time() < end_time:
        time.sleep(interval)
        new_scroll_position = driver.execute_script("return window.pageYOffset;")
        if new_scroll_position == last_scroll_position:
            return True
        last_scroll_position = new_scroll_position
    return False


def log_info(message):
    with print_lock:
        print(Fore.CYAN + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}" + Style.RESET_ALL)


def log_success(message):
    with print_lock:
        print(Fore.GREEN + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}" + Style.RESET_ALL)


def log_warning(message):
    with print_lock:
        print(Fore.YELLOW + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}" + Style.RESET_ALL)


def log_error(message):
    with print_lock:
        print(Fore.RED + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}" + Style.RESET_ALL)


def log_loading_light(message):
    with print_lock:
        print(Fore.LIGHTBLUE_EX + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}" + Style.RESET_ALL)


def log_important(message):
    with print_lock:
        print(Fore.LIGHTGREEN_EX + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}" + Style.RESET_ALL)


def wait_for_element(driver, xpath, timeout=20, retries=3):
    """等待元素可见并可点击，支持重试"""
    for i in range(retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            return element
        except Exception as e:
            print(f"尝试 {i+1}/{retries} 失败，错误：{e}")
            time.sleep(2)
    raise Exception(f"元素 {xpath} 在 {retries} 次尝试后仍未找到！")


def login_to_system(driver, username_text, password_text):
    """登入系統"""
    loading_xpath = "/html/body/div[2]/div/p"
    loading_xpath2 = "/html/body/div[2]/div/i"
    
    driver.get("https://ad.jfw-win.com/#/agent-login")
    driver.maximize_window()

    username = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="請輸入帳號"]'))
    )
    username.click()
    time.sleep(0.5)
    username.clear()
    username.send_keys(username_text)

    password = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="請輸入密碼"]'))
    )
    password.click()
    time.sleep(0.5)
    password.clear()
    password.send_keys(password_text)

    login = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "login-btn")]'))
    )
    login.click()

    time.sleep(5)
    log_loading_light("登入中...\n")
    time.sleep(8)

    try:
        current_url = driver.current_url
        log_info(f"當前頁面: {current_url}")
    except Exception as e:
        log_error(f"瀏覽器連接已斷開: {e}")
        raise
    
    return loading_xpath, loading_xpath2


def safe_click(driver, by, locator, retries=3):
    """封装点击操作，自动重试避免 stale element 错误"""
    wait = WebDriverWait(driver, 10)
    for attempt in range(retries):
        try:
            element = wait.until(EC.element_to_be_clickable((by, locator)))
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
            return True
        except StaleElementReferenceException:
            print(f"⚠️ 第 {attempt+1} 次尝试点击失败，重新查找元素...")
    print("无法点击元素，请检查网页状态。")
    return False


def navigate_to_players(driver, loading_xpath, loading_xpath2):
    """導航到直屬玩家頁面，返回 True 表示有資料，False 表示無資料"""
    log_info("正在跳轉到帳戶管理頁面...")
    driver.get("https://ad.jfw-win.com/#/agent/user-manage/agent-user")

    WebDriverWait(driver, 180).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="app"]'))
    )
    time.sleep(1)

    # 等待第一層 loading 消失
    WebDriverWait(driver, 180).until(
        EC.invisibility_of_element_located((By.XPATH, loading_xpath))
    )
    WebDriverWait(driver, 180).until(
        EC.invisibility_of_element_located((By.XPATH, loading_xpath2))
    )
    time.sleep(2)

    # 等待 loading mask 完全消失
    try:
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "el-loading-mask"))
        )
    except:
        pass
    
    time.sleep(1)

    # 確認元素可見
    element = WebDriverWait(driver, 180).until(
        EC.visibility_of_element_located((By.XPATH, '//div[@role="tablist"]//div[@id="tab-gameUser"]'))
    )

    # 確認元素可點擊
    player = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@role="tablist"]//div[@id="tab-gameUser"]'))
    )
    
    # 再次確認沒有 loading 遮罩
    try:
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "el-loading-mask"))
        )
    except:
        pass
    
    time.sleep(1)
    log_loading_light("點選[直屬玩家]\n")
    
    # 使用 JavaScript 點擊，避免被遮擋
    try:
        player.click()
    except:
        # 如果普通點擊失敗，使用 JavaScript 強制點擊
        driver.execute_script("arguments[0].click();", player)
    
    # 等待點擊後的 loading 消失
    WebDriverWait(driver, 180).until_not(
        EC.presence_of_element_located((By.XPATH, loading_xpath))
    )
    
    # 再次等待可能的 loading mask
    try:
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "el-loading-mask"))
        )
    except:
        pass
    
    time.sleep(2)
    
    # 檢查是否有「無內容」圖片
    try:
        no_content = driver.find_element(By.XPATH, '//img[contains(@src, "icon_no content")]')
        if no_content:
            log_warning("此帳號底下無會員資料，跳過處理")
            return False
    except:
        pass  # 沒有找到無內容圖片，表示有資料
    
    # 檢查是否有分頁控制元素（有資料才會有）
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="app-main"]/section/footer/div[2]/div/span[2]/div/div/span/span/i'))
        )
        time.sleep(1)
        return True  # 有分頁元素，表示有資料
    except:
        log_warning("此帳號底下無會員資料，跳過處理")
        return False


def set_page_size_to_500(driver):
    """切换到 500 条/页"""
    try:
        log_info("目前頁面會員均已符合條件")
        log_info("切換至 500條/頁 檢查")
        page_dropdown = WebDriverWait(driver, 180).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="app-main"]/section/footer/div[2]/div/span[2]/div/div/span/span/i'))
        )
        time.sleep(1)
        page_dropdown.click()

        page_option_500 = WebDriverWait(driver, 180).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[1]/div[1]/ul/li[5]/span'))
        )
        time.sleep(1)
        page_option_500.click()
        time.sleep(3)
        log_info("已切换至 500 条/页")
    except Exception as e:
        log_error(f"切换至 500 条/页失败: {e}")


def process_member_add_balance(driver, account_name, member_balance, num, loading_xpath):
    """處理上分邏輯"""
    log_info(f"餘額：{member_balance} ，低於目標金額： {num} ，準備上分...")

    time.sleep(3)

    if click_with_retry(driver,
                        '//*[@id="app-main"]/section/main/div[2]/div[1]/div[2]/div[6]/div[5]/div/button[3]',
                        '/html/body/div[2]/div/div[2]/div[1]/div/div[3]/div[2]'):
        log_info("點擊額度設定成功")
    else:
        log_warning("點擊額度設定失敗，已嘗試多次")

    if click_with_retry(driver, '/html/body/div[2]/div/div[2]/div[1]/div/div[3]/div[2]',
                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/div[2]/input'):
        log_info("點擊點數分配成功")
    else:
        log_warning("點擊點數分配失敗，已嘗試多次")

    try:
        adjust = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/div[2]/input'))
        )
        time.sleep(0.2)
        adjust.clear()
        time.sleep(0.2)
        adjust.send_keys(str(num - member_balance))
        time.sleep(0.2)
    except Exception as e:
        log_warning(f"调整余额失败：{e}")

    if click_with_retry(driver,
                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[5]/div[2]',
                        '//*[@id="app-main"]/section/main/div[2]/div[1]/div[2]'):
        log_warning(f"{account_name} ，上分成功\n")
    else:
        log_warning(f"{account_name} ，上分失败，已尝试多次")

    WebDriverWait(driver, 180).until_not(
        EC.presence_of_element_located((By.XPATH, loading_xpath))
    )
    time.sleep(2)


def process_member_deduct_balance(driver, account_name, member_balance, num, loading_xpath):
    """處理扣分邏輯"""
    log_info(f"{account_name} 餘額 {member_balance} 大於 {num}，準備扣分")

    time.sleep(3)

    if click_with_retry(driver,
                        '//*[@id="app-main"]/section/main/div[2]/div[1]/div[2]/div[6]/div[5]/div/button[3]',
                        '/html/body/div[2]/div/div[2]/div[1]/div/div[3]/div[2]'):
        log_info("点击额度设定成功")
    else:
        log_warning("点击额度设定失败")

    time.sleep(1)

    if click_with_retry(driver, '/html/body/div[2]/div/div[2]/div[1]/div/div[3]/div[2]',
                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[2]/div[2]/label[2]/span[1]/span'):
        log_info("点击点数分配成功")
    else:
        log_warning("点击点数分配失败")

    time.sleep(1)

    if click_with_retry(driver,
                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[2]/div[2]/label[2]/span[1]/span',
                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/div[2]/input'):
        log_info("点击减少余额成功")
    else:
        log_warning("点击减少余额失败")

    time.sleep(1)

    try:
        adjust = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[3]/div[2]/input'))
        )
        time.sleep(0.2)
        adjust.clear()
        time.sleep(0.2)
        adjust.send_keys(str(member_balance - num))
        log_info("调整余额成功")
    except Exception as e:
        log_warning(f"调整余额失败: {e}")

    time.sleep(0.2)

    if click_with_retry(driver,
                        '//*[@id="app-main"]/section/main/div[2]/div[2]/div[1]/div/div[2]/div[3]/div[5]/div[2]',
                        '//*[@id="app-main"]/section/main/div[2]/div[1]/div[2]'):
        log_warning(f"{account_name} 扣分成功\n")
    else:
        log_warning(f"{account_name} 扣分失败")

    WebDriverWait(driver, 180).until_not(
        EC.presence_of_element_located((By.XPATH, loading_xpath))
    )
    time.sleep(2)


def return_to_players_page(driver):
    """返回玩家列表頁面"""
    log_important("返回代理帳號")
    driver.get("https://ad.jfw-win.com/#/agent/user-manage/agent-user")
    time.sleep(4)

    log_important("跳轉[直屬玩家]頁面\n")

    max_attempts = 3
    attempt = 0
    clicked = False

    while attempt < max_attempts and not clicked:
        try:
            player = WebDriverWait(driver, 180).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@role="tablist"]//div[@id="tab-gameUser"]'))
            )
            time.sleep(1)
            player.click()
            clicked = True
        except Exception as e:
            attempt += 1
            log_important(f"点击直属玩家失败，尝试 {attempt} 次")
            if attempt < max_attempts:
                time.sleep(2)
            else:
                log_important("点击直属玩家失败，已达最大重试次数。")

    WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app-main"]/section/footer/div[2]/div/span[2]/div/div/span/span/i'))
    )
    time.sleep(1)


def process_all_members(driver, num, loading_xpath):
    """處理所有會員的上下分邏輯"""
    with print_lock:
        print("")
        print(Fore.MAGENTA + "腳本開始執行!\n" + Style.RESET_ALL)
    log_loading_light("重新整理页面\n")

    page_size_50_checked = False
    switching_to_500 = False
    all_members_checked = False
    processed_accounts = set()  # 記錄已處理過的帳號

    player = WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@role="tablist"]//div[@id="tab-gameUser"]'))
    )
    time.sleep(1)
    player.click()

    while not all_members_checked:
        try:
            WebDriverWait(driver, 180).until_not(
                EC.presence_of_element_located((By.XPATH, loading_xpath))
            )

            log_loading_light("正在取得會員帳號\n")
            time.sleep(5)

            accounts = WebDriverWait(driver, 180).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="app-main"]/section/main/div[4]/div[2]/div/div/div[1]/div[1]/div[2]/div[2]'))
            )

            buttons = []
            for idx in range(1, 1000):
                try:
                    xpath = f'//*[@id="agent-bbox-id"]/div[2]/div/div[{idx}]/div[1]/div[3]/div[1]'
                    button = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    buttons.append(button)
                except:
                    break

            if not accounts or not buttons:
                log_success("所有會員上分任務完成！\n")
                break

            processed = False
            skipped_accounts = set()

            for idx, (account, button) in enumerate(zip(accounts, buttons), start=1):
                try:
                    account_name = account.text.strip()

                    # 檢查是否已處理過此帳號
                    if account_name in processed_accounts:
                        log_info(f"{account_name} 已處理過，跳過")
                        continue

                    agent_type_xpath = f'//*[@id="agent-bbox-id"]/div[2]/div/div[{idx}]/div[1]/div[2]/div[1]/div[2]'
                    agent_type_element = WebDriverWait(driver, 180).until(
                        EC.presence_of_element_located((By.XPATH, agent_type_xpath))
                    )
                    agent_type = agent_type_element.text.strip()

                    if agent_type == "信用代理":
                        if account_name not in skipped_accounts:
                            skipped_accounts.add(account_name)
                        continue

                    balance_xpath = f'//*[@id="agent-bbox-id"]/div[2]/div/div[{idx}]/div[1]/div[2]/div[5]/div[2]'
                    balance_element = WebDriverWait(driver, 180).until(
                        EC.presence_of_element_located((By.XPATH, balance_xpath))
                    )
                    member_balance = int(float(balance_element.text.replace(",", "")))

                    if member_balance == num:
                        skipped_accounts.add(account_name)
                        processed_accounts.add(account_name)  # 記錄為已處理
                        log_info(f"{account_name} 餘額已符合目標 {num}，標記為已處理")
                        continue

                    log_info(f"{account_name}，類型：『現金代理』，餘額: {member_balance}，開始處理")

                    # 處理上分
                    if member_balance < num:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        if wait_for_scroll_end(driver):
                            time.sleep(2)
                            button.click()
                            log_info("準備上分")
                        else:
                            log_info("滾動超時未結束")

                        process_member_add_balance(driver, account_name, member_balance, num, loading_xpath)
                        processed_accounts.add(account_name)  # 記錄為已處理
                        log_success(f"{account_name} 已完成上分並標記為已處理")
                        return_to_players_page(driver)

                        if switching_to_500:
                            set_page_size_to_500(driver)

                        processed = True
                        break

                    # 處理扣分
                    if member_balance > num:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        if wait_for_scroll_end(driver):
                            time.sleep(2)
                            button.click()
                            log_info("準備扣除")
                        else:
                            log_info("滾動超時未結束")

                        process_member_deduct_balance(driver, account_name, member_balance, num, loading_xpath)
                        processed_accounts.add(account_name)  # 記錄為已處理
                        log_success(f"{account_name} 已完成扣分並標記為已處理")
                        return_to_players_page(driver)

                        if switching_to_500:
                            set_page_size_to_500(driver)

                        processed = True
                        break

                except Exception as e:
                    log_error(f"{account_name} 處理失敗: {e}")
                    continue

            if not processed:
                if not page_size_50_checked:
                    set_page_size_to_500(driver)
                    page_size_50_checked = True
                    switching_to_500 = True
                    continue
                elif switching_to_500:
                    log_success("所有直屬會員已檢查完畢，無需繼續補/扣分。\n")
                    all_members_checked = True
                else:
                    log_success("所有直屬會員餘額均符合要求，無需補/扣分。\n")
                    all_members_checked = True

        except Exception as e:
            log_error(f"發生錯誤: {e}")
            break

    log_success("所有會員任務完成！")


def process_single_account(username_text, password_text, num):
    """處理單一帳號的完整流程"""
    driver = None
    try:
        with print_lock:
            print(f"\n{'='*50}")
            print(Fore.YELLOW + f"開始處理帳號: {username_text} | 目標金額: {num}" + Style.RESET_ALL)
            print(f"{'='*50}\n")
        
        driver = init_driver()
        loading_xpath, loading_xpath2 = login_to_system(driver, username_text, password_text)
        
        # 導航到玩家頁面，檢查是否有資料
        has_data = navigate_to_players(driver, loading_xpath, loading_xpath2)
        
        if has_data:
            # 有資料才處理會員
            process_all_members(driver, num, loading_xpath)
            with print_lock:
                print(f"\n{'='*50}")
                print(Fore.GREEN + f"帳號 {username_text} 處理完成！" + Style.RESET_ALL)
                print(f"{'='*50}\n")
        else:
            # 無資料，直接跳過
            with print_lock:
                print(f"\n{'='*50}")
                print(Fore.YELLOW + f"帳號 {username_text} 無會員資料，已跳過" + Style.RESET_ALL)
                print(f"{'='*50}\n")
        
    except Exception as e:
        log_error(f"處理帳號 {username_text} 時發生錯誤: {e}")
    finally:
        if driver:
            try:
                with print_lock:
                    print("\033[1;33m正在關閉瀏覽器...\033[0m")
                driver.quit()
                log_success(f"帳號 {username_text} 瀏覽器已關閉")
            except Exception as e:
                log_error(f"關閉帳號 {username_text} 瀏覽器時發生錯誤: {e}")


def main():
    """主程式入口"""
    init_environment()
    
    # 載入所有帳號
    accounts = load_accounts()
    
    if not accounts:
        print("帳號列表為空，請檢查 用戶資訊.txt 是否有有效資料")
        input("按 Enter 結束...")
        sys.exit(1)
    
    # 設定每批次處理的帳號數量
    BATCH_SIZE = 5
    total_accounts = len(accounts)
    total_batches = (total_accounts + BATCH_SIZE - 1) // BATCH_SIZE  # 向上取整
    
    print(f"\n{'='*50}")
    print(Fore.CYAN + f"共有 {total_accounts} 個帳號待處理" + Style.RESET_ALL)
    print(Fore.CYAN + f"將分 {total_batches} 批次執行，每批次最多 {BATCH_SIZE} 個帳號" + Style.RESET_ALL)
    print(f"{'='*50}\n")
    
    # 分批處理帳號
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_accounts)
        batch_accounts = accounts[start_idx:end_idx]
        
        print(f"\n{'='*50}")
        print(Fore.YELLOW + f"開始執行第 {batch_num + 1}/{total_batches} 批次" + Style.RESET_ALL)
        print(Fore.YELLOW + f"本批次處理 {len(batch_accounts)} 個帳號" + Style.RESET_ALL)
        print(f"{'='*50}\n")
        
        # 建立本批次的執行緒列表
        threads = []
        
        # 為本批次的每個帳號建立執行緒
        for username_text, password_text, num in batch_accounts:
            thread = threading.Thread(
                target=process_single_account,
                args=(username_text, password_text, num),
                name=f"Thread-{username_text}"
            )
            threads.append(thread)
            thread.start()
            
            # 稍微錯開啟動時間，避免同時初始化太多瀏覽器
            time.sleep(2)
        
        # 等待本批次所有執行緒完成
        for thread in threads:
            thread.join()
        
        print(f"\n{'='*50}")
        print(Fore.GREEN + f"第 {batch_num + 1}/{total_batches} 批次完成！" + Style.RESET_ALL)
        print(f"{'='*50}\n")
        
        # 如果不是最後一批，稍作休息
        if batch_num < total_batches - 1:
            print(Fore.CYAN + "等待 5 秒後執行下一批次...\n" + Style.RESET_ALL)
            time.sleep(5)
    
    print("\n" + "="*50)
    print(Fore.GREEN + "所有帳號處理完畢！" + Style.RESET_ALL)
    print("="*50)
    
    input("\n按 Enter 結束...")


if __name__ == "__main__":
    main()
