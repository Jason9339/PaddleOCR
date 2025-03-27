from paddleocr import PaddleOCR, draw_ocr
from tools.infer.utility import resize_img, text_visual
from PIL import Image
import json
import os
import sys
import glob
import numpy as np
import cv2

# 確保使用本地修改的版本
sys.path.insert(0, os.path.abspath('.'))  # 假設在 PaddleOCR 根目錄運行

# 添加調試資訊驗證使用的是修改後的代碼
print("Current working directory:", os.getcwd())
print("sys.path:", sys.path)

# 函數：只繪製文字框和編號
def draw_boxes_only(image, boxes, drop_score=0.5, scores=None):
    """
    只在原圖上繪製文字框和編號，不添加右側文字結果
    """
    if isinstance(image, Image.Image):
        img_array = np.array(image).copy()
    else:
        img_array = image.copy()
    
    box_num = len(boxes)
    for i in range(box_num):
        if scores is not None and (scores[i] < drop_score or np.isnan(scores[i])):
            continue
        
        # 繪製框
        box = np.reshape(np.array(boxes[i]), [-1, 1, 2]).astype(np.int64)
        img_array = cv2.polylines(img_array, [box], True, (255, 0, 0), 2)
        
        # 獲取右上角坐標
        right_top_x = box[1][0][0]
        right_top_y = box[1][0][1]
        
        # 在右上角添加編號
        cv2.putText(img_array, str(i + 1), (right_top_x, right_top_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    
    return img_array

# 初始化 OCR，設置 merge_repeated=False 以適應 SVTR 模型
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="chinese_cht",
    rec_char_dict_path="ppocr/utils/dict/chinese_cht_dict.txt",
    rec_algorithm="SVTR_LCNet",
    merge_repeated=False,
    use_gpu=True
)

# 設置圖片來源和結果輸出目錄
img_dir = "../history_image"
output_dir = "../result/json"
output_img_dir = "../result/img"
output_onlybox_dir = "../result/img_onlybox"

# 確保輸出目錄存在
os.makedirs(output_dir, exist_ok=True)
os.makedirs(output_img_dir, exist_ok=True)
os.makedirs(output_onlybox_dir, exist_ok=True)

# 獲取所有 JPG 和 PNG 圖片文件
image_files = glob.glob(os.path.join(img_dir, "*.jpg")) + glob.glob(os.path.join(img_dir, "*.png"))
if not image_files:
    print(f"錯誤：在 '{img_dir}' 中找不到 JPG 或 PNG 圖片")
    sys.exit(1)

print(f"找到 {len(image_files)} 個圖片（JPG 和 PNG）")

# 處理每張圖片
for img_path in image_files:
    img_filename = os.path.basename(img_path)
    print(f"\n正在處理圖片: {img_path}")

    # 執行 OCR
    result = ocr.ocr(img_path, cls=True)

    # 檢查結果是否包含預期的字段
    if not result or not result[0]:
        print(f"警告：'{img_filename}' 的 OCR 結果為空")
        continue

    # 保存為 JSON 以便分析
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
            
            # 添加字符詳細信息（Top-3 候選字）
            if len(word_info[1]) > 2 and word_info[1][2]:
                word_json["char_details"] = word_info[1][2]
            
            page_json.append(word_json)
        result_json.append(page_json)

    # 保存結果
    json_filename = os.path.splitext(img_filename)[0] + "_ocr_result.json"
    output_json_path = os.path.join(output_dir, json_filename)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=2)

    print(f"\n結果已保存至 {output_json_path}")

    # 可視化結果
    try:
        # 讀取原始圖像
        image = Image.open(img_path).convert("RGB")
        
        # 處理第一頁的結果（如果有多頁）
        page_result = result[0]
        if page_result is not None:
            boxes = [line[0] for line in page_result]
            txts = [line[1][0] for line in page_result]
            scores = [float(line[1][1]) for line in page_result]
            char_details_list = []
            for line in page_result:
                if len(line[1]) > 2:
                    char_details = line[1][2]
                    char_details_list.append(char_details)
                else:
                    char_details_list.append(None)
            
            # 指定字體路徑
            font_path = "../fonts/chinese_cht.ttf"
            
            # 確認字體文件存在
            if not os.path.exists(font_path):
                print(f"警告：找不到字體文件 '{font_path}'，嘗試使用其他字體")
                potential_font_paths = [
                    "./simfang.ttf",
                    "./fonts/NotoSansCJK-Regular.ttc",
                    "./fonts/chinese_cht.ttf",
                    "/usr/share/fonts/truetype/arphic/uming.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ]
                font_path = None  # 如果找不到任何字體，使用系統默認字體
                for path in potential_font_paths:
                    if os.path.exists(path):
                        font_path = path
                        print(f"使用替代字體: {font_path}")
                        break
                if font_path is None:
                    print("警告：找不到任何字體，使用系統默認字體")
            
            # 1. 產生只有框和編號的結果
            try:
                only_boxes_img = draw_boxes_only(image, boxes, scores=scores)
                onlybox_filename = os.path.splitext(img_filename)[0] + "_onlybox.png"
                onlybox_path = os.path.join(output_onlybox_dir, onlybox_filename)
                if isinstance(only_boxes_img, np.ndarray):
                    only_boxes_img = Image.fromarray(only_boxes_img)
                only_boxes_img.save(onlybox_path)
                print(f"只有框和編號的結果已保存至 {onlybox_path}")
            except Exception as e:
                print(f"警告：生成只有框和編號的結果時出錯 - {e}")
                import traceback
                traceback.print_exc()
            
            # 2. 使用預設的 draw_ocr 函數繪製視覺化結果
            try:
                im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)
                vis_filename = os.path.splitext(img_filename)[0] + "_result.png"
                vis_path = os.path.join(output_img_dir, vis_filename)
                if isinstance(im_show, np.ndarray):
                    im_show = Image.fromarray(im_show)
                im_show.save(vis_path)
                print(f"視覺化結果已保存至 {vis_path}")
            except Exception as e:
                print(f"警告：使用 draw_ocr 生成視覺化結果時出錯 - {e}")
                import traceback
                traceback.print_exc()
                
        else:
            print("警告：第一頁未識別到文字，無法生成視覺化結果")
    except Exception as e:
        print(f"警告：生成視覺化結果時出錯 - {e}")
        import traceback
        traceback.print_exc()

print("\n所有圖片處理完成!")