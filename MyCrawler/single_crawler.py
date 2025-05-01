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
import sys

# 初始化Selenium瀏覽器
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(options=options)

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
        expand_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
        )
        safe_click(expand_button, "Clicking expand button (擴充)")
        time.sleep(1)

        fullpage_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='toggle-full-page']"))
        )
        safe_click(fullpage_button, "Clicking toggle full page button")
        time.sleep(1)

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
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='關閉'][aria-label='關閉']"))
        )
        safe_click(close_button, "Clicking close button to exit fullscreen")
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
    return id_match.group(1) if id_match else None

# 提取 IIIF info.json URL 並獲取圖片 URL
def get_image_url(collection, info_id):
    try:
        info_url = f"https://contentdm.lib.nccu.edu.tw/iiif/2/{collection}:{info_id}/info.json"
        print(f"Fetching IIIF info.json from: {info_url}")
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
        filename = os.path.join(download_dir, f"rec_{rec_number}_id_{image_id}.jpg")
        print(f"Downloading image to: {filename}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(image_url, headers=headers, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Successfully downloaded image: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

# 處理單一URL的主函數
def process_single_url(target_url):
    try:
        print(f"Opening URL: {target_url}")
        driver.get(target_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.ItemImage-expandButton"))
        )
        print("Page loaded successfully")

        # 提取URL中的資訊
        current_url = driver.current_url
        image_id = extract_id_from_url(current_url)
        if not image_id:
            print(f"Cannot extract ID from URL: {current_url}")
            return

        rec_match = re.search(r'rec/(\d+)', current_url)
        rec_number = rec_match.group(1) if rec_match else f"id_{image_id}"
        collection_match = re.search(r'collection/([^/]+)', current_url)
        collection = collection_match.group(1) if collection_match else "lclma"

        print(f"Processing: rec_{rec_number}, URL ID: {image_id}")

        # 模擬滾動頁面
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

        # 第三遍：遍歷並下載所有圖片
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
                    image_url = get_image_url(collection, info_id)
                    if image_url:
                        download_image(image_url, rec_number, compound_image_id)
                    else:
                        print(f"Failed to get image URL for info ID: {info_id}, URL ID: {compound_image_id}")
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

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("Browser closed.")

# 從命令列獲取URL並執行
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python single_crawler.py <URL>")
        print("Example: python single_crawler.py https://contentdm.lib.nccu.edu.tw/digital/collection/lclma/id/3666/rec/39")
        sys.exit(1)

    target_url = sys.argv[1]
    process_single_url(target_url)