import pygame
from mazegen import MazeGenerator
from mur_aff import laby_dessin, creation_niveau, brouillard

pygame.init()
ecran  = pygame.display.set_mode((800, 600))
horloge = pygame.time.Clock()
couleurs = [(255, 105, 180), (0, 200, 255), (255, 220, 0), (120, 255, 120), (255, 0, 0), (255, 0, 255)]
affiche = ["= COMMANDES =", "c : Skin", "↑ : Haut", "↓ : Bas", "← : Gauche", "→ : Droite"]
index_couleur = 0
en_cours = True
joueur_x = 0
joueur_y = 0
niveau = 0
maze = creation_niveau(niveau)
screamer = False
police = pygame.font.SysFont("segoeuisymbol", 20)
image = pygame.image.load("image.png")
image = pygame.transform.scale(image, (800, 600))
son = pygame.mixer.Sound("cri.wav")
while en_cours:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            en_cours = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                case = maze.grid[joueur_y][joueur_x]
                if not case & 1:
                    joueur_y -=1
            if event.key == pygame.K_DOWN:
                case = maze.grid[joueur_y][joueur_x]
                if not case & 4:
                    joueur_y +=1
            if event.key == pygame.K_LEFT:
                case = maze.grid[joueur_y][joueur_x]
                if not case & 8:
                    joueur_x -=1
            if event.key == pygame.K_RIGHT:
                case = maze.grid[joueur_y][joueur_x]
                if not case & 2:
                    joueur_x +=1
            if event.key == pygame.K_c:
                index_couleur = (index_couleur + 1) % len(couleurs)
    ecran.fill((0, 0, 0))
    laby_dessin(ecran, maze.grid)
    if niveau >= 1:
        brouillard(ecran, maze.grid, joueur_x, joueur_y)
    index_a = 450
    for val in affiche:
        texte = police.render(val, True, (255, 255, 255))
        ecran.blit(texte, (0, index_a))
        index_a += 25
    sortie_x = len(maze.grid[0]) - 1
    sortie_y = len(maze.grid) - 1
    sx = sortie_x * 30 + 5
    sy = sortie_y * 30 + 5
    pygame.draw.rect(ecran, (255, 240, 150), (sx, sy, 20, 20))
    px = joueur_x * 30 + 5
    py = joueur_y * 30 + 5
    pygame.draw.rect(ecran, couleurs[index_couleur], (px, py, 20, 20))
    if joueur_x == sortie_x and joueur_y == sortie_y and not screamer:
        if niveau == 2:
            screamer = True
            son.play()
        else:
            niveau += 1
            maze = creation_niveau(niveau)
            joueur_y = 0
            joueur_x = 0
    if screamer:
        ecran.blit(image, (0, 0))
    pygame.display.flip()
    horloge.tick(60)

pygame.quit()
    