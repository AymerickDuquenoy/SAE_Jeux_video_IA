"""
NavigationSystem - Déplacement des unités le long de leur chemin.

RÈGLES CRITIQUES :
1. Suit le chemin A* nœud par nœud (mouvements axiaux uniquement)
2. S'arrête pour combattre une TROUPE ennemie (Target.type == "unit")
3. Continue vers la case d'attaque même si pyramide à portée
4. La pyramide est attaquée seulement quand l'unité est ARRIVÉE

IA DIFFÉRENCIÉE :
- Momie/Dromadaire: s'arrêtent pour combattre les troupes
- Sphinx: ne s'arrête JAMAIS pour les troupes, fonce vers la pyramide
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
    Déplacement propre style jeu flash.
    Mouvements strictement axiaux (horizontal OU vertical, jamais diagonal).
    """

    def __init__(self, *, arrive_radius: float = 0.15, min_speed: float = 0.0, attack_range: float = 2.0):
        super().__init__()
        self.arrive_radius = float(arrive_radius)
        self.min_speed = float(min_speed)
        self.attack_range = float(attack_range)  # Synchronisé avec TargetingSystem et CombatSystem

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

            # Identifier le type d'unité
            unit_type = self._get_unit_type(ent)

            # Vérifier si on doit combattre une TROUPE
            # SPHINX (L) ne s'arrête JAMAIS - il fonce vers la pyramide
            should_stop_for_combat = False
            should_align_for_combat = False
            align_target_pos = None
            
            if unit_type != "L" and esper.has_component(ent, Target):
                target = esper.component_for_entity(ent, Target)
                
                # Gérer les TROUPES ennemies (pas pyramides)
                if target.type == "unit":
                    tid = int(target.entity_id)
                    if esper.entity_exists(tid):
                        try:
                            th = esper.component_for_entity(tid, Health)
                            tt = esper.component_for_entity(tid, Transform)
                            if not th.is_dead:
                                ax, ay = transform.pos
                                bx, by = tt.pos
                                dx = bx - ax
                                dy = by - ay
                                dist = math.hypot(dx, dy)
                                
                                # Alignement axial (tolérance 0.5 comme CombatSystem)
                                aligned_h = abs(dy) <= 0.5  # Même Y
                                aligned_v = abs(dx) <= 0.5  # Même X
                                aligned = aligned_h or aligned_v
                                
                                if dist <= self.attack_range:
                                    if aligned:
                                        # À portée ET aligné → s'arrêter et tirer
                                        should_stop_for_combat = True
                                    else:
                                        # À portée mais PAS aligné → se déplacer pour s'aligner
                                        should_align_for_combat = True
                                        align_target_pos = (bx, by)
                                elif dist <= 0.5:
                                    # Très proche → évite de passer à travers
                                    should_stop_for_combat = True
                        except:
                            pass

            if should_stop_for_combat:
                velocity.vx = 0.0
                velocity.vy = 0.0
                continue

            # Se déplacer pour s'aligner avec la cible (au lieu de suivre le chemin)
            if should_align_for_combat and align_target_pos:
                ax, ay = transform.pos
                bx, by = align_target_pos
                dx = bx - ax
                dy = by - ay
                
                # Choisir le mouvement qui nous aligne le plus vite
                # Si on n'est pas aligné horizontalement (|dy| > 0.5), bouger en Y
                # Sinon bouger en X pour se rapprocher
                if abs(dy) > 0.5:
                    # Pas aligné en Y → bouger verticalement
                    dirx = 0.0
                    diry = 1.0 if dy > 0 else -1.0
                elif abs(dx) > 0.5:
                    # Pas aligné en X → bouger horizontalement
                    dirx = 1.0 if dx > 0 else -1.0
                    diry = 0.0
                else:
                    # Déjà aligné, ne devrait pas arriver ici
                    velocity.vx = 0.0
                    velocity.vy = 0.0
                    continue
                
                # Vitesse effective (terrain)
                eff_speed = max(self.min_speed, float(speed.base) * float(speed.mult_terrain))
                if esper.has_component(ent, TerrainEffect):
                    terr = esper.component_for_entity(ent, TerrainEffect)
                    eff_speed = terr.apply(eff_speed)
                
                velocity.vx = dirx * eff_speed
                velocity.vy = diry * eff_speed
                
                # Mouvement
                new_x = ax + velocity.vx * dt
                new_y = ay + velocity.vy * dt
                transform.pos = (new_x, new_y)
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
            # On bouge soit en X soit en Y, jamais les deux
            if abs(dx) > abs(dy):
                # Mouvement horizontal prioritaire
                dirx = 1.0 if dx > 0 else -1.0
                diry = 0.0
            else:
                # Mouvement vertical
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
