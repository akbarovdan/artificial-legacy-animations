HEIGHT = 3
WIDTH = 3

grid = [[0, 0, 1], [0, 1, 0], [1, 0, 0]]

def count_neighbors(grid, r, c):
    count = 0
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue

            nr = r + dr
            nc = c + dc

            if 0 <= nr < HEIGHT and 0 <= nc < WIDTH:
                count += grid[nr][nc]
    return count

def get_next_generation(grid):
    new_grid = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]