import cv2
import numpy as np
from pathlib import Path

# =========================================================================
# КОНФИГУРАЦИЯ
# =========================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_VIDEO = str(SCRIPT_DIR / "input_birds.mp4")
OUTPUT_VIDEO = str(SCRIPT_DIR / "birds_tracked_cut.mp4")

CUT_TO_BLACK_SEC = 2.5   # Секунда жесткого переключения на черный фон
THRESHOLD_VAL = 110      

# Цвет: Неоновый оранжевый/персиковый (#FAB387) - идеально пробивает серый туман
NEON_COLOR = (135, 179, 250) 

MAX_TRACKED_BIRDS = 40   # Лимит рамок, чтобы не делать из видео нечитаемую кашу

# =========================================================================
# ОСНОВНОЙ КОНВЕЙЕР
# =========================================================================
def main():
    cap = cv2.VideoCapture(INPUT_VIDEO)
    if not cap.isOpened():
        raise FileNotFoundError(f"Не удалось открыть файл: {INPUT_VIDEO}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    cut_frame = int(CUT_TO_BLACK_SEC * fps)
    
    # Отсекаем нижние 30% экрана (вода и кусты)
    sky_limit_y = int(height * 0.70)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (width, height))

    prev_gray = None
    frame_idx = 0

    print("Запуск рендеринга. Жесткий кат на черном фоне...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. ЖЕСТКИЙ КАТ В ЧЕРНЫЙ ФОН
        if frame_idx >= cut_frame:
            rendered_frame = np.zeros_like(frame)
            rendered_frame[:] = [12, 8, 8] # #08080C (Catppuccin Crust)
        else:
            rendered_frame = frame.copy()

        # 2. ДЕТЕКЦИЯ (ОТСЕКАЕМ КУСТЫ)
        _, thresh = cv2.threshold(gray, THRESHOLD_VAL, 255, cv2.THRESH_BINARY_INV)
        thresh[sky_limit_y:, :] = 0  # Игнорируем всё, что ниже линии неба
        
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 3. ОПТИЧЕСКИЙ ПОТОК (ВЕКТОРЫ СКОРОСТИ)
        flow_vectors = None
        if prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None, 
                pyr_scale=0.5, levels=2, winsize=13, 
                iterations=2, poly_n=5, poly_sigma=1.1, flags=0
            )
            flow_vectors = flow

        # 4. ФИЛЬТРАЦИЯ ОТ КАШИ (Оставляем только самые четкие цели)
        valid_contours = [c for c in contours if 5 < cv2.contourArea(c) < 800]
        # Сортируем по размеру и берем только топ-N птиц
        top_contours = sorted(valid_contours, key=cv2.contourArea, reverse=True)[:MAX_TRACKED_BIRDS]

        # 5. ОТРИСОВКА ОРАНЖЕВОГО НЕОНА
        for cnt in top_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w // 2, y + h // 2

            cv2.rectangle(rendered_frame, (x, y), (x + w, y + h), NEON_COLOR, 1)

            if flow_vectors is not None and cy < height and cx < width:
                vx = flow_vectors[cy, cx, 0] * 4.0
                vy = flow_vectors[cy, cx, 1] * 4.0
                end_pt = (int(cx + vx), int(cy + vy))
                cv2.line(rendered_frame, (cx, cy), end_pt, (255, 255, 255), 1)

        out.write(rendered_frame)
        prev_gray = gray
        frame_idx += 1

        if frame_idx % 30 == 0:
            print(f"Обработано: {frame_idx}/{total_frames} кадров")

    cap.release()
    out.release()
    print(f"Готово: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()