
import time


class SokoBot:
    def solveSokobanPuzzle(self, width, height, mapData, itemsData):
        start_time = time.time()
        #Initialize the boards and the pieces to use
        walls = set()
        targets = set()
        crates = set()
        player = None

        # Parse board layout from the txt
        for r in range(height):
            for c in range(width):
                if mapData[r][c] == '#':
                    walls.add((r, c))
                elif mapData[r][c] == '.':
                    targets.add((r, c))

                if itemsData[r][c] == '@':
                    player = (r, c)
                elif itemsData[r][c] == '$':
                    crates.add((r, c))

        targets = tuple(sorted(targets))

        # Simple Corner Check: Non-target wall corners
        corner = set()
        for r in range(height):
            for c in range(width):
                if (r, c) in walls or (r, c) in targets:
                    continue
                up = (r - 1, c) in walls
                down = (r + 1, c) in walls
                left = (r, c - 1) in walls
                right = (r, c + 1) in walls
                if (up or down) and (left or right):
                    corner.add((r, c))

        return ""
