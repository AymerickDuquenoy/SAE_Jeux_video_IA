"""
AIBehaviorSystem - Comportements IA différenciés par type d'unité.

Selon le Game Design SAÉ:
- Momie (S): Flocking - se déplace en groupe, attaque ensemble
- Dromadaire (M): Tank solo - priorité aux ennemis, protège les alliés
- Sphinx (L): Siège - ignore les troupes, cible directement la pyramide

Ce système modifie les priorités de ciblage et de mouvement.
"""
import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress


class AIBehaviorSystem(esper.Processor):
    """
    Applique des comportements IA différenciés selon le type d'unité.
    """

    def __init__(self, pyramid_ids: set[int]):
        super().__init__()
        self.pyramid_ids = set(int(x) for x in pyramid_ids)
        
        # Paramètres flocking pour Momies
        self.flocking_radius = 2.5
        self.flocking_strength = 0.3
        
        # Paramètres tank pour Dromadaires
        self.tank_aggro_range = 3.0
        
        # Paramètres siège pour Sphinx
        self.siege_ignore_units = True

    def _get_unit_type(self, stats: UnitStats) -> str:
        """Détermine le type d'unité (S/M/L) basé sur les stats."""
        # Basé sur la puissance: S=8, M=12, L=18
        power = getattr(stats, 'power', 0)
        if power <= 9:
            return "S"  # Momie
        elif power <= 14:
            return "M"  # Dromadaire
        else:
            return "L"  # Sphinx

    def _apply_flocking(self, eid: int, t: Transform, team: Team, dt: float):
        """
        Momies: légère attraction vers les alliés proches.
        Simule un comportement de meute.
        """
        if not esper.has_component(eid, Velocity):
            return
            
        vel = esper.component_for_entity(eid, Velocity)
        ax, ay = t.pos
        
        # Trouver les alliés proches
        allies_dx = 0.0
        allies_dy = 0.0
        ally_count = 0
        
        for other_eid, (ot, oteam, ostats) in esper.get_components(Transform, Team, UnitStats):
            if other_eid == eid:
                continue
            if oteam.id != team.id:
                continue
            
            # Seulement les autres Momies
            if self._get_unit_type(ostats) != "S":
                continue
                
            ox, oy = ot.pos
            d = math.hypot(ox - ax, oy - ay)
            
            if 0.5 < d < self.flocking_radius:
                allies_dx += (ox - ax) / d
                allies_dy += (oy - ay) / d
                ally_count += 1
        
        # Appliquer une légère attraction
        if ally_count > 0:
            allies_dx /= ally_count
            allies_dy /= ally_count
            
            # Modifier légèrement la vélocité
            vel.vx += allies_dx * self.flocking_strength * dt * 10
            vel.vy += allies_dy * self.flocking_strength * dt * 10

    def _apply_tank_behavior(self, eid: int, t: Transform, team: Team, stats: UnitStats):
        """
        Dromadaires: agressif, cherche activement les combats.
        Priorité aux ennemis les plus proches même hors de la lane.
        """
        # Le Dromadaire garde son comportement standard mais avec
        # une portée de détection légèrement augmentée
        # (géré dans TargetingSystem via stats)
        pass

    def _apply_siege_behavior(self, eid: int, t: Transform, team: Team):
        """
        Sphinx: ignore les troupes ennemies, va directement à la pyramide.
        On retire la cible si c'est une unité (pas une pyramide).
        """
        if not esper.has_component(eid, Target):
            return
            
        target = esper.component_for_entity(eid, Target)
        
        # Si la cible est une unité (pas pyramide), on l'ignore
        if target.type == "unit":
            esper.remove_component(eid, Target)

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            # Vérifier que l'unité est vivante
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue

            unit_type = self._get_unit_type(stats)

            if unit_type == "S":
                # Momie: flocking
                self._apply_flocking(eid, t, team, dt)
                
            elif unit_type == "M":
                # Dromadaire: tank (comportement standard amélioré)
                self._apply_tank_behavior(eid, t, team, stats)
                
            elif unit_type == "L":
                # Sphinx: siège - ignore les unités
                self._apply_siege_behavior(eid, t, team)
