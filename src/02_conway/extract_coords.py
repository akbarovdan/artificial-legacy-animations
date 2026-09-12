import os
import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_PATH = os.path.join(SCRIPT_DIR, "conway.png")
OUT_PATH = os.path.join(SCRIPT_DIR, "conway_matrix.npy")

# 1. Загружаем и переводим в ч/б
img = Image.open(IMG_PATH).convert("L")

# 2. Идеальный размер сетки для Manim (48x48)
GRID_SIZE = 48
img_resized = img.resize((GRID_SIZE, GRID_SIZE), Image.Resampling.LANCZOS)
arr = np.array(img_resized)

# 3. Черные точки (лицо, борода, контуры) делаем живыми клетками (1)
# Белый фон делаем мертвыми клетками (0)
grid = (arr < 130).astype(int)

np.save(OUT_PATH, grid)
print(f"Успех! Файл сохранен: {OUT_PATH}")
print(f"Всего живых пикселей в лице Конвея: {np.sum(grid)}")