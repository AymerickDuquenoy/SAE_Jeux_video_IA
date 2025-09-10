# 🎮 SAÉ – Jeux Vidéo

## 👥 Équipe
- **DELHAYE Florian**
- **CONDETTE Albin**
- **CHAGOT Manon**
- **DOUILLY Quentin**
- **DUQUENOY Aymerick**

---

## 📌 Contexte
Projet SAÉ (BUT Info 3 – S5). Objectifs :
- Développer un **moteur de jeu** (affichage, I/O, événements).
- Intégrer une **IA** (perception → décision → action).
- Respecter le **cadre commun** : base fixe, 3 types d’unités, ressources, 3 zones de terrain.

---

## 🏺 Concept 
Deux pyramides s’affrontent dans le désert égyptien. Détruisez la pyramide adverse en gérant vos ressources (**“coups de fouet”**) et en déployant trois types d’unités :

| Type | Unité | Rôle | Vitesse | Blindage | Puissance | Coût (≈ P) |
|---|---|---|---|---|---|---|
| L | **Momie** | Essaim rapide / harcèlement | Élevée | Faible | Faible | Bas |
| M | **Chameau blindé (avec soldat)** | Polyvalent / ligne | Moyenne | Moyenne | Moyenne | Moyen |
| S | **Sphinx** | Siège lourd / tank | Faible | Élevé | Élevée | Élevé |

**Règles d’équilibrage (cadre SAÉ)** :  
- \( V + B = \text{constante} \) (trade-off vitesse/blindage).  
- \( C = k \times P \) (coût proportionnel à la puissance).

---

## 🗺️ Terrain
Carte rectangulaire composée de :
- **Sable normal**
- **Sable mouvant**
- **Zones interdites**

---

## 💰 Ressource — “Coups de fouet”
- Production passive dans le temps.
- Gain à la destruction d’unités ennemies.
- Dépense à la création d’unités.


## 🛠️ Tech / Démarrer
- **Langage** : Python (moteur + IA).


