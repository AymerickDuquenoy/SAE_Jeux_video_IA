# Terrains et obstacles

Le champ de bataille est composé de différents types de terrains et d’obstacles.

Ces éléments influencent le déplacement des unités et leur vitesse.

## Types de terrain

### Désert

![Désert](images/Sable.png)

Le désert est le terrain standard du jeu.

Il ne modifie pas les caractéristiques des unités.  
Les unités peuvent y atteindre leur vitesse maximale.

Caractéristiques :

| Effet | Valeur |
|-----|-------|
| Vitesse des unités | Maximale |


### Sables mouvants

![Sables mouvants](images/Sable%20mouvant.png)

Les sables mouvants ralentissent les unités qui les traversent.

Caractéristiques :

| Effet | Valeur |
|-----|-------|
| Vitesse des unités | Vitesse maximale / 2 |

## Obstacles

Certains éléments du décor sont infranchissables et bloquent le passage des unités.

Les unités doivent alors contourner ces éléments.

### Cactus

![Cactus](images/Cactus.png)

Les cactus bloquent totalement le déplacement des unités.

### Palmiers

![Palmiers](images/Palmier.png)

Les palmiers bloquent également le déplacement des unités.

## Impact sur le déplacement

La présence de terrains et d’obstacles modifie les trajectoires des unités.

Les unités :

- évitent automatiquement les obstacles ;
- adaptent leur chemin en fonction du terrain ;
- peuvent être ralenties selon la zone traversée.
