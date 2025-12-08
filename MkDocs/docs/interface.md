# Interface du jeu

L’interface d’Antique War est conçue pour rester claire tout en montrant les informations importantes pour prendre des décisions rapides.

---

## Vue d’ensemble

L’écran de jeu se compose généralement de :

1. **Zone de jeu centrale**  
   - Le désert, les pyramides, les unités alliées et ennemies, les obstacles.

2. **Zone d’informations (souvent en haut)**  
   - Nombre de 𓍯 disponibles.
   - Niveau de votre pyramide.
   - Points de vie de votre pyramide (barre de vie ou chiffre).

3. **Barre d’actions (souvent en bas)**  
   - Boutons pour invoquer :
     - Momie
     - Dromadaire blindé
     - Sphinx
   - Bouton pour améliorer la pyramide (si assez de ressources).

---

## Resource HUD (𓍯)

L’interface affiche en permanence :

- le **nombre actuel de 𓍯**,
- l’évolution au fil du temps (vous voyez le chiffre augmenter).

Vous devez garder un œil dessus pour savoir :

- quand vous pouvez invoquer une unité,
- quand vous pouvez améliorer la pyramide.

---

## Retour visuel

La plupart des actions ont un retour visuel clair :

- invocation d’une unité → apparition près de votre pyramide ;
- amélioration → changement visuel de la pyramide (selon l’implémentation) ou indication de niveau ;
- évènements → effets visibles (tempête, nuée, etc.).

L’interface est volontairement simple pour que vous puissiez vous concentrer sur la stratégie.
