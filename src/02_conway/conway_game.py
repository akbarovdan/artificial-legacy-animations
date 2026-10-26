import os
import random
import sys
import time

# 1. Автоматически определяем размер окна терминала
# terminal_size возвращает (колонки, строки)
cols, lines = os.get_terminal_size()

# Клетки рисуем как "█ " (два символа в ширину), поэтому ширина поля = cols // 2
WIDTH = cols // 2
HEIGHT = lines - 1  # Оставляем одну строчку запаса снизу


def create_random_grid():
    """Создает сетку под размер терминала со случайными живыми клетками (шанс 20%)."""
    grid = []
    for _ in range(HEIGHT):
        row = []
        for _ in range(WIDTH):
            row.append(1 if random.random() < 0.20 else 0)
        grid.append(row)
    return grid


def count_neighbors(grid, r, c):
    """Считает соседей.

    Использует остаток от деления (%), чтобы мир был «пончиком»:
    клетка, уходящая за правый край, видит соседей на левом краю!
    """
    count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue

            # Оператор % зацикливает координаты по краям поля
            nr = (r + dr) % HEIGHT
            nc = (c + dc) % WIDTH

            count += grid[nr][nc]
    return count


def get_next_generation(grid):
    """Рассчитывает следующее поколение по правилам Конвея."""
    new_grid = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

    for r in range(HEIGHT):
        for c in range(WIDTH):
            neighbors = count_neighbors(grid, r, c)
            cell = grid[r][c]

            if cell == 1 and (neighbors == 2 or neighbors == 3):
                new_grid[r][c] = 1
            elif cell == 0 and neighbors == 3:
                new_grid[r][c] = 1
            else:
                new_grid[r][c] = 0

    return new_grid


def print_grid(grid):
    """Быстрый и плавный вывод без мерцания."""
    # \033[H возвращает курсор в левый верхний угол (строка 1, столбец 1)
    output = "\033[H"

    for row in grid:
        # Для живой клетки печатаем белые квадраты, для мертвой — пустоту
        line = "".join("█ " if cell == 1 else "  " for cell in row)
        output += line + "\n"

    sys.stdout.write(output)
    sys.stdout.flush()


def main():
    # Очищаем экран один раз при старте
    os.system("clear")

    # Скрываем курсор, чтобы он не мелькал перед глазами
    sys.stdout.write("\033[?25l")

    grid = create_random_grid()

    try:
        while True:
            print_grid(grid)
            grid = get_next_generation(grid)
            time.sleep(0.05)  # Скорость анимации (чем меньше число, тем быстрее)
    except KeyboardInterrupt:
        # При нажатии Ctrl + C вежливо возвращаем курсор на место
        sys.stdout.write("\033[?25h")
        print("\nИгра остановлена!")


if __name__ == "__main__":
    main()