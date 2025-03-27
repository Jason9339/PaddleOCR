from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
import time
import re
import requests
import os
import json

# 初始化Selenium瀏覽器
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(options=options)

# 從搜尋頁面開始
search_url = "https://contentdm.lib.nccu.edu.tw/digital/collection/lclma/search"
driver.get(search_url)
print("Opened search page, waiting for it to load...")

# 追蹤已處理的ID，避免重複
processed_ids = set()
max_items = 100  # 設定最大項目數

# 創建下載目錄
download_dir = "downloaded_images"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 安全點擊元素的函數
def safe_click(element, message="Clicking element"):
    try:
        print(message)
        driver.execute_script("arguments[0].scrollIntoView(true);", element)  # 滾動到元素
        driver.execute_script("arguments[0].click();", element)
        time.sleep(2)  # 模擬人類操作，增加延遲
        return True
    except Exception as e:
        print(f"Error clicking element: {e}")
        return False

# 模擬滾動頁面
def scroll_page():
    try:
        print("Simulating page scroll to trigger visibility...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    except Exception as e:
        print(f"Error scrolling page: {e}")

# 進入全螢幕模式的函數
def enter_fullscreen_mode():
    try:
        # 第一步：點擊「擴充」按鈕
        expand_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
        )
        safe_click(expand_button, "Clicking expand button (擴充)")
        time.sleep(1)

        # 第二步：點擊「Toggle full page」按鈕
        fullpage_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='toggle-full-page']"))
        )
        safe_click(fullpage_button, "Clicking toggle full page button")
        time.sleep(1)

        # 確認是否進入全螢幕模式
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[title='關閉'][aria-label='關閉']"))
        )
        print("Successfully entered full-screen mode")
        return True
    except Exception as e:
        print(f"Error entering full-screen mode: {e}")
        return False

# 退出全螢幕模式的函數
def exit_fullscreen():
    try:
        # 優先使用「關閉」按鈕
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='關閉'][aria-label='關閉']"))
        )
        safe_click(close_button, "Clicking close button to exit fullscreen")
        # 等待頁面穩定，例如等待「擴充」按鈕重新出現
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
        )
        print("Successfully exited full-screen mode")
        time.sleep(1)
        return True
    except TimeoutException:
        print("Could not find close button, trying toggle button as fallback")
        try:
            fullpage_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='toggle-full-page']"))
            )
            safe_click(fullpage_button, "Exiting full-screen mode by clicking toggle button")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
            )
            print("Successfully exited full-screen mode using toggle button")
            time.sleep(1)
            return True
        except TimeoutException:
            print("Could not find toggle button, trying ESC key as fallback")
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
                )
                print("Successfully exited full-screen mode using ESC key")
                time.sleep(1)
                return True
            except:
                print("ESC key fallback also failed")
                return False
    except Exception as e:
        print(f"Error exiting full-screen: {e}")
        return False

# 提取 URL 中的 ID
def extract_id_from_url(url):
    id_match = re.search(r'id/(\d+)', url)
    if id_match:
        return id_match.group(1)
    return None

# 提取 IIIF info.json URL 並獲取圖片 URL
def get_image_url(collection, info_id):
    try:
        # 構造 IIIF info.json URL
        info_url = f"https://contentdm.lib.nccu.edu.tw/iiif/2/{collection}:{info_id}/info.json"
        print(f"Fetching IIIF info.json from: {info_url}")

        # 發送請求獲取 info.json
        response = requests.get(info_url)
        response.raise_for_status()
        info_data = response.json()
        base_url = info_data.get("@id")
        if not base_url:
            print("Could not find @id in info.json")
            return None
        image_url = f"{base_url}/full/full/0/default.jpg"
        print(f"Extracted image URL: {image_url}")
        return image_url
    except Exception as e:
        print(f"Error fetching image URL for info ID {info_id}: {e}")
        return None

# 下載圖片
def download_image(image_url, rec_number, image_id):
    try:
        # 構建檔案名稱
        filename = os.path.join(download_dir, f"rec_{rec_number}_id_{image_id}.jpg")
        print(f"Downloading image to: {filename}")

        # 發送請求下載圖片
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers, stream=True)
        response.raise_for_status()

        # 儲存圖片
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Successfully downloaded image: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

try:
    # 第一步：點擊第一個搜尋結果以開始瀏覽
    try:
        print("Looking for search results...")
        search_results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.SearchResult-container[href*='/digital/collection/lclma/id/']"))
        )
        if search_results:
            print(f"Found {len(search_results)} search results. Clicking the first one...")
            safe_click(search_results[0], "Clicking first search result")
            WebDriverWait(driver, 10).until(
                EC.url_contains("/digital/collection/lclma/id/")
            )
        else:
            print("No search results found. Please check the website structure.")
            raise Exception("No search results found")
    except Exception as e:
        print(f"Error finding search results: {e}")
        raise

    # 開始逐一處理項目
    items_processed = 0

    while items_processed < max_items:
        # 獲取當前URL並提取記錄資訊
        current_url = driver.current_url
        print(f"Current URL: {current_url}")

        # 提取ID
        image_id = extract_id_from_url(current_url)
        if not image_id:
            print(f"Cannot extract ID from URL: {current_url}")
            break

        # 提取記錄編號
        rec_match = re.search(r'rec/(\d+)', current_url)
        if rec_match:
            rec_number = rec_match.group(1)
        else:
            rec_number = f"id_{image_id}"

        # 檢查是否重複
        if image_id in processed_ids:
            print(f"Already processed ID {image_id}, skipping to next")
        else:
            processed_ids.add(image_id)
            items_processed += 1

            print(f"Processing item #{items_processed}: rec_{rec_number}, image ID: {image_id}")

            # 提取collection
            collection_match = re.search(r'collection/([^/]+)', current_url)
            collection = collection_match.group(1) if collection_match else "lclma"

            # 模擬滾動頁面，確保元素可見
            scroll_page()

            # 第一遍：計算圖片張數並記錄所有圖片的 URL ID
            processed_compound_ids = set()
            compound_item_ids = []
            compound_item_count = 0

            print("First pass: Counting total images in this record...")
            while True:
                current_url = driver.current_url
                compound_image_id = extract_id_from_url(current_url)
                if compound_image_id:
                    if compound_image_id in processed_compound_ids:
                        print(f"Compound item ID {compound_image_id} already processed, stopping first pass")
                        break
                    processed_compound_ids.add(compound_image_id)
                    compound_item_count += 1
                    compound_item_ids.append(compound_image_id)
                    print(f"Found compound item {compound_item_count}, ID: {compound_image_id}")
                else:
                    print("Could not extract compound item ID from URL")
                    break

                try:
                    next_image_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button.cdm-btn.btn.btn-default span.fa-chevron-right"))
                    )
                except TimeoutException:
                    print("No next image button found, assuming single image or end of images")
                    break

                if next_image_button.get_attribute("disabled"):
                    print("Next image button is disabled, reached the last image")
                    break

                old_url = driver.current_url
                safe_click(next_image_button, "Clicking next image button")
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.current_url != old_url
                    )
                    print("Successfully switched to next image")
                except TimeoutException:
                    print("URL didn't change after clicking next image button, reached the last image")
                    break

            print(f"Total compound items in this record: {compound_item_count}")

            # 計算第一張圖片的 info.json ID
            first_info_id = int(image_id) - compound_item_count
            print(f"Calculated first info.json ID: {first_info_id}")

            # 第二遍：回到第一張圖片
            print("Second pass: Navigating back to the first image...")
            while True:
                try:
                    prev_image_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button.cdm-btn.btn.btn-default span.fa-chevron-left"))
                    )
                except TimeoutException:
                    print("No previous image button found, assuming already at the first image")
                    break

                if prev_image_button.get_attribute("disabled"):
                    print("Previous image button is disabled, reached the first image")
                    break

                old_url = driver.current_url
                safe_click(prev_image_button, "Clicking previous image button")
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.current_url != old_url
                    )
                    print("Successfully switched to previous image")
                except TimeoutException:
                    print("URL didn't change after clicking previous image button, reached the first image")
                    break

            # 第三遍：遍歷並下載圖片
            processed_compound_ids = set()
            current_index = 0

            print("Third pass: Downloading images...")
            while current_index < compound_item_count:
                current_url = driver.current_url
                compound_image_id = extract_id_from_url(current_url)
                if compound_image_id:
                    if compound_image_id in processed_compound_ids:
                        print(f"Compound item ID {compound_image_id} already processed, stopping download pass")
                        break
                    processed_compound_ids.add(compound_image_id)
                    print(f"Processing compound item {current_index + 1}, URL ID: {compound_image_id}")

                    # 計算該圖片的 info.json ID
                    info_id = first_info_id + current_index
                    print(f"Calculated info.json ID for this image: {info_id}")

                    # 進入全螢幕模式
                    entered_fullscreen = enter_fullscreen_mode()
                    if entered_fullscreen:
                        # 提取圖片 URL 並下載
                        image_url = get_image_url(collection, info_id)
                        if image_url:
                            download_image(image_url, rec_number, compound_image_id)
                        else:
                            print(f"Failed to get image URL for info ID: {info_id}, URL ID: {compound_image_id}, skipping...")
                        exit_fullscreen()
                    else:
                        print(f"Failed to enter full-screen mode for compound item {current_index + 1}")

                    current_index += 1
                else:
                    print("Could not extract compound item ID from URL")
                    break

                if current_index >= compound_item_count:
                    break

                try:
                    next_image_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button.cdm-btn.btn.btn-default span.fa-chevron-right"))
                    )
                except TimeoutException:
                    print("No next image button found, assuming end of images")
                    break

                if next_image_button.get_attribute("disabled"):
                    print("Next image button is disabled, reached the last image")
                    break

                old_url = driver.current_url
                safe_click(next_image_button, "Clicking next image button")
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: d.current_url != old_url
                    )
                    print("Successfully switched to next image")
                except TimeoutException:
                    print("URL didn't change after clicking next image button, reached the last image")
                    break

            print(f"Processed {current_index} compound items in total for this record")

        # 導航到下一個記錄
        try:
            print("Looking for next record button...")
            # 等待「下一頁」按鈕存在
            next_button = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemViewPager-angle[aria-label='Next record']"))
            )

            # 直接使用 JavaScript 點擊
            old_url = driver.current_url
            driver.execute_script("arguments[0].click();", next_button)
            print("Clicked next record button using JavaScript")

            # 等待頁面內容變化
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.current_url != old_url
                )
            except TimeoutException:
                print("URL didn't change, checking if page content updated...")
                # 如果URL未變化，檢查頁面內容是否更新（例如記錄ID變化）
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
                )
                new_url = driver.current_url
                new_id_match = extract_id_from_url(new_url)
                if new_id_match and new_id_match != image_id:
                    print("Page content updated even though URL structure didn't change")
                else:
                    print("Page content didn't update, might be at the last record")
                    break

            # 翻頁後等待頁面載入
            print("Waiting for next record to load...")
            time.sleep(5)  # 增加等待時間至 5 秒
            scroll_page()  # 模擬滾動，觸發可能的 JavaScript 事件
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
                )
                print("Next record loaded")
            except TimeoutException:
                print("Next record not fully loaded after navigating")

        except TimeoutException as e:
            print(f"Timeout waiting for next record button to be present: {e}")
            print("Might be at the last record or button is not in DOM")
            break
        except Exception as e:
            print(f"Error navigating to next record: {e}")
            break

except KeyboardInterrupt:
    print("\nScript interrupted by user. Closing browser...")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()
    print("Browser closed. Navigation test completed.")