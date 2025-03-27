import paddleocr
print(paddleocr.__file__) 

from paddleocr import PaddleOCR, draw_ocr

from PIL import Image

# 初始化 OCR（指定繁體中文模型）
ocr = PaddleOCR(lang="chinese_cht")

# 圖片路徑（.png 格式）
img_path = "../ch/test_image.jpg"

# 執行 OCR
result = ocr.ocr(img_path)

# 檢查 OCR 結果
for idx, line in enumerate(result):
    for word_info in line:
        print(f"第 {idx+1} 行: {word_info}")

# 讀取圖片
image = Image.open(img_path).convert("RGB")

# **修正 scores 的計算方式**
boxes = [word_info[0] for line in result for word_info in line]
txts = [word_info[1][0] for line in result for word_info in line]
scores = [float(word_info[1][1]) for line in result for word_info in line]  # 確保是 float

# 指定字型（請確保字型檔案存在）
font_path = "../fonts/chinese_cht.ttf"

# 繪製 OCR 結果
im_show = draw_ocr(image, boxes, txts, scores, font_path=font_path)

# 儲存結果
im_show = Image.fromarray(im_show)
im_show.save("../result.png")

print("OCR 識別完成，結果已儲存為 result.png")