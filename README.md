# 🌀 Maze Game

Un petit jeu de labyrinthe en Python avec **pygame** pour troller ses amies. Le but trouver la sortie… de plus en plus dans le noir.

Le jeu réutilise le générateur de labyrinthe créé pendant le projet **A-Maze-ing** à l'École 42 : chaque partie génère des labyrinthes différents.

## 🎮 Le jeu

Guide ton personnage jusqu'à la **lumière jaune** en bas à droite du labyrinthe pour passer au niveau suivant.

| Niveau | Taille | Difficulté |
|--------|--------|------------|
| 0 | Petit | Tout est visible, parfait pour prendre en main les touches |
| 1 | Grand | 🌫️ Brouillard : tu ne vois que 2 cases autour de toi |
| 2 | Grand | 🌫️ Brouillard… et une petite surprise à la fin 👀 |

## ⌨️ Commandes

| Touche | Action |
|--------|--------|
| ↑ | Monter |
| ↓ | Descendre |
| ← | Aller à gauche |
| → | Aller à droite |
| C | Changer la couleur du personnage |

## 🛠️ Installation

Il te faut **Python 3.10+**.

1. Clone le dépôt :
   ```
   git clone <lien-du-repo>
   cd <nom-du-dossier>
   ```

2. Installe pygame :
   ```
   pip install pygame
   ```
   Sur Windows, si `pip` ne marche pas :
   ```
   py -m pip install pygame
   ```

3. Lance le jeu :
   ```
   python3 jeu.py
   ```
   Sur Windows :
   ```
   py jeu.py
   ```

## 📁 Structure

```
├── jeu.py        # Boucle principale : déplacements, niveaux, affichage
├── mur_aff.py    # Dessin des murs, du labyrinthe et du brouillard
├── mazegen.py    # Générateur de labyrinthe (projet A-Maze-ing)
├── image.png     # 🤫
└── cri.wav       # 🤫
```

## 🧠 Comment ça marche

- **Génération** : chaque case du labyrinthe est stockée comme un nombre où chaque bit représente un mur (Nord = 1, Est = 2, Sud = 4, Ouest = 8).
- **Collisions** : avant chaque déplacement, le jeu vérifie si un mur bloque la direction choisie.
- **Brouillard** : les cases trop loin du joueur sont recouvertes d'un carré noir à chaque frame.

## 🙌 Crédits

- Générateur de labyrinthe : projet **A-Maze-ing** (École 42), réalisé en binôme
- Jeu : fait avec amour et beaucoup de `Ctrl+S` oubliés 😄
