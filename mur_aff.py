import pygame
from mazegen import MazeGenerator

def mur_nord(ecran, x, y):
    px = x * 30
    py = y * 30
    pygame.draw.line(ecran, (255, 255, 255), (px, py),(px + 30, py), 2)


def mur_sud(ecran, x, y):
    px = x * 30
    py = y * 30
    pygame.draw.line(ecran, (255, 255, 255), (px, py + 30),(px + 30, py + 30), 2)


def mur_ouest(ecran, x, y):
    px = x * 30
    py = y * 30
    pygame.draw.line(ecran, (255, 255, 255), (px, py),(px, py + 30), 2)


def mur_est(ecran, x, y):
    px = x * 30
    py = y * 30
    pygame.draw.line(ecran, (255, 255, 255), (px + 30, py),(px + 30, py + 30), 2)


def laby_dessin(ecran, grid):
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            case = grid[y][x]
            if case & 1:
                mur_nord(ecran, x, y)
            if case & 4:
                mur_sud(ecran, x, y)
            if case & 2:
                mur_est(ecran, x, y)
            if case & 8:
                mur_ouest(ecran, x, y)


def creation_niveau(niveau):
    if niveau == 0:
        largeur = 10
        hauteur = 8
    else:
        largeur = 20
        hauteur = 15
    maze = MazeGenerator(width=largeur, height=hauteur, entry=(0, 0), exit_=(largeur -1, hauteur -1), perfect=True)
    maze.generate()
    return maze


def brouillard(ecran, grid, joueur_x, joueur_y):
    for y in range(len(grid)):
        for x in range(len(grid[0])):
            px = x * 30
            py = y * 30
            distance_x = abs(x - joueur_x)
            distance_y = abs(y - joueur_y)
            if distance_x > 2 or distance_y > 2:
                pygame.draw.rect(ecran, (0, 0, 0), (px, py, 30, 30))