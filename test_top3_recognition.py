from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import json
import os
import sys

# 確保使用本地修改的版本
sys.path.insert(0, os.path.abspath('.'))  # 假設在PaddleOCR根目錄運行

# 添加調試資訊驗證使用的是修改後的代碼
print("Current working directory:", os.getcwd())
# print("sys.path:", sys.path)

# 初始化 OCR
ocr = PaddleOCR(use_angle_cls=True, lang="chinese_cht")

# 測試圖片路徑
img_path = "../ch/test_image2.jpg" 

# 確認圖片是否存在
if not os.path.exists(img_path):
    print(f"錯誤：找不到測試圖片'{img_path}'")
    sys.exit(1)

print(f"正在處理圖片: {img_path}")


# 執行 OCR
result = ocr.ocr(img_path, cls=True)

# 檢查結果是否包含預期的字段
if not result:
    print("錯誤：OCR結果為空")
    sys.exit(1)

# 輸出解析結果
print("\n===== 完整OCR結果 =====")
for idx, page_result in enumerate(result):
    print(f"\n第 {idx+1} 頁:")
    if page_result is None:
        print("  此頁未識別到文字")
        continue
    
    for line_idx, line in enumerate(page_result):
        print(f"\n  行 {line_idx+1}:")
        
        # 基本信息
        box = line[0]
        text = line[1][0]
        score = line[1][1]
        print(f"    框位置: {box}")
        print(f"    識別文本: {text}")
        print(f"    整體置信度: {score}")
        
        # 字符詳細信息
        if len(line) > 3 and line[3]:
            print(f"\n    -- 字符詳細信息 --")
            for char_detail in line[3]:
                print(f"      字符: '{char_detail['char']}'")
                if 'position' in char_detail:
                    print(f"      位置: {char_detail['position']}")
                if 'time_step' in char_detail:
                    print(f"      時間步: {char_detail['time_step']}")
                print(f"      前3候選:")
                for cand in char_detail['top3']:
                    print(f"        - '{cand['char']}' (置信度: {cand['score']:.4f})")
        print("-" * 70)

# 保存為JSON以便分析
result_json = []

for page_idx, page_result in enumerate(result):
    if page_result is None:
        result_json.append(None)
        continue
    
    page_json = []
    for word_info in page_result:
        word_json = {
            "box": word_info[0],
            "text": word_info[1][0],
            "score": float(word_info[1][1])
        }
        
        # 添加字符詳細信息
        if len(word_info) > 3 and word_info[3]:
            word_json["char_details"] = word_info[3]
        
        page_json.append(word_json)
    result_json.append(page_json)

# 保存結果
output_path = "../ocr_top3_result.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result_json, f, ensure_ascii=False, indent=2)

print(f"\n結果已保存至 {output_path}")

# 可視化結果（僅顯示主要識別結果）
try:
    image = Image.open(img_path).convert("RGB")
    
    # 處理第一頁的結果（如果有多頁）
    page_result = result[0]
    if page_result is not None:
        boxes = [line[0] for line in page_result]
        txts = [line[1][0] for line in page_result]
        scores = [float(line[1][1]) for line in page_result]
        
        # 指定字體路徑
        font_path = "../fonts/chinese_cht.ttf"
        
        # 確認字體文件存在
        if not os.path.exists(font_path):
            print(f"警告：找不到字體文件'{font_path}'，嘗試使用系統默認字體")
            # 嘗試尋找系統中的字體
            potential_font_paths = [
                "./simfang.ttf",
                "./fonts/NotoSansCJK-Regular.ttc",
                "./fonts/chinese_cht.ttf",
                "/usr/share/fonts/truetype/arphic/uming.ttc"
            ]
            for path in potential_font_paths:
                if os.path.exists(path):
                    font_path = path
                    print(f"使用替代字體: {font_path}")
                    break
        
        # 繪製 OCR 結果
        im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)
        
        # 保存結果
        vis_path = "../result_with_top3.png"
        im_show = Image.fromarray(im_show)
        im_show.save(vis_path)
        print(f"視覺化結果已保存至 {vis_path}")
    else:
        print("警告：第一頁未識別到文字，無法生成視覺化結果")
except Exception as e:
    print(f"警告：生成視覺化結果時出錯 - {e}")

print("\n測試完成!")