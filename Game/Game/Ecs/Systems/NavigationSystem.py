"""
NavigationSystem - Déplacement des unités le long de leur chemin.

RÈGLES :
1. Suit le chemin A* nœud par nœud
2. S'arrête pour combattre une TROUPE ennemie (Target.type == "unit") à portée
3. Continue vers la pyramide sinon
4. TOUTES les unités s'arrêtent pour combattre (y compris Sphinx)
"""
import math
import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.terrain_effect import TerrainEffect
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats


class NavigationSystem(esper.Processor):
    """
    Déplacement des unités.
    S'arrête quand une cible ennemie est à portée.
    """

    def __init__(self, *, arrive_radius: float = 0.15, min_speed: float = 0.0, attack_range: float = 2.0, align_tolerance: float = 0.7):
        super().__init__()
        self.arrive_radius = float(arrive_radius)
        self.min_speed = float(min_speed)
        self.attack_range = float(attack_range)
        self.align_tolerance = float(align_tolerance)  # Non utilisé mais gardé pour compatibilité

    def _get_unit_type(self, ent: int) -> str:
        """Détermine le type d'unité (S/M/L) basé sur les stats."""
        if not esper.has_component(ent, UnitStats):
            return "S"
        stats = esper.component_for_entity(ent, UnitStats)
        power = getattr(stats, 'power', 0)
        if power <= 9:
            return "S"  # Momie
        elif power <= 14:
            return "M"  # Dromadaire
        else:
            return "L"  # Sphinx

    def process(self, dt: float):
        if dt <= 0:
            return

        for ent, (gpos, path, prog) in esper.get_components(GridPosition, Path, PathProgress):
            transform = self._ensure_transform(ent, gpos)
            velocity = self._ensure_velocity(ent)
            speed = self._ensure_speed(ent)

            # Vérifier si on doit s'arrêter pour combattre
            # TOUTES les unités s'arrêtent pour combattre
            should_stop = False
            
            if esper.has_component(ent, Target):
                target = esper.component_for_entity(ent, Target)
                
                # S'arrêter uniquement pour les TROUPES ennemies (pas pyramides)
                if target.type == "unit":
                    tid = int(target.entity_id)
                    if esper.entity_exists(tid):
                        try:
                            th = esper.component_for_entity(tid, Health)
                            tt = esper.component_for_entity(tid, Transform)
                            if not th.is_dead:
                                ax, ay = transform.pos
                                bx, by = tt.pos
                                dist = math.hypot(bx - ax, by - ay)
                                
                                # À portée d'attaque → s'arrêter
                                if dist <= self.attack_range:
                                    should_stop = True
                        except:
                            pass

            if should_stop:
                velocity.vx = 0.0
                velocity.vy = 0.0
                continue

            # Suivre le chemin normal
            nodes = getattr(path, "noeuds", None)
            if not nodes or prog.index >= len(nodes) - 1:
                # Chemin terminé - s'arrêter
                velocity.vx = 0.0
                velocity.vy = 0.0
                continue

            # Prochain nœud à atteindre
            target_node = nodes[prog.index + 1]
            tx, ty = transform.pos
            gx, gy = float(target_node.x), float(target_node.y)

            dx = gx - tx
            dy = gy - ty
            dist = math.hypot(dx, dy)

            # Arrivé au nœud (snap)
            if dist <= self.arrive_radius:
                transform.pos = (gx, gy)
                gpos.x, gpos.y = int(target_node.x), int(target_node.y)
                prog.index += 1

                if prog.index >= len(nodes) - 1:
                    # Chemin terminé
                    velocity.vx = 0.0
                    velocity.vy = 0.0
                continue

            # Direction vers le nœud - MOUVEMENT AXIAL STRICT
            if abs(dx) > abs(dy):
                dirx = 1.0 if dx > 0 else -1.0
                diry = 0.0
            else:
                dirx = 0.0
                diry = 1.0 if dy > 0 else -1.0

            # Vitesse effective (terrain)
            eff_speed = max(self.min_speed, float(speed.base) * float(speed.mult_terrain))

            if esper.has_component(ent, TerrainEffect):
                terr = esper.component_for_entity(ent, TerrainEffect)
                eff_speed = terr.apply(eff_speed)

            velocity.vx = dirx * eff_speed
            velocity.vy = diry * eff_speed

            step = eff_speed * dt
            
            # Anti-overshoot
            if step >= dist:
                transform.pos = (gx, gy)
                gpos.x, gpos.y = int(target_node.x), int(target_node.y)
                prog.index += 1
                if prog.index >= len(nodes) - 1:
                    velocity.vx = 0.0
                    velocity.vy = 0.0
                continue

            # Mouvement normal
            new_x = tx + velocity.vx * dt
            new_y = ty + velocity.vy * dt
            transform.pos = (new_x, new_y)

    def _ensure_transform(self, ent: int, gpos: GridPosition) -> Transform:
        if esper.has_component(ent, Transform):
            return esper.component_for_entity(ent, Transform)
        t = Transform(pos=(float(gpos.x), float(gpos.y)))
        esper.add_component(ent, t)
        return t

    def _ensure_velocity(self, ent: int) -> Velocity:
        if esper.has_component(ent, Velocity):
            return esper.component_for_entity(ent, Velocity)
        v = Velocity()
        esper.add_component(ent, v)
        return v

    def _ensure_speed(self, ent: int) -> Speed:
        if esper.has_component(ent, Speed):
            return esper.component_for_entity(ent, Speed)
        s = Speed()
        esper.add_component(ent, s)
        return s
