# Game/Ecs/Systems/NavigationSystem.py
import math
import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.velocity import Velocity
from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.terrain_effect import TerrainEffect


class NavigationSystem(esper.Processor):
    """
    Déplacement "propre jeu flash" :
    - suit un Path (liste de GridPosition)
    - mouvement constant (pas d'inertie) => pas de glisse / pas de diagonales à cause de l'accel
    - anti-overshoot => snap sur le nœud
    - NE SUPPRIME PAS Path / PathProgress (LaneRouteSystem doit pouvoir replanifier)
    """

    def __init__(self, *, arrive_radius: float = 0.12, min_speed: float = 0.0):
        super().__init__()
        self.arrive_radius = float(arrive_radius)
        self.min_speed = float(min_speed)

    def process(self, dt: float):
        if dt <= 0:
            return

        for ent, (gpos, path, prog) in esper.get_components(GridPosition, Path, PathProgress):
            transform = self._ensure_transform(ent, gpos)
            velocity = self._ensure_velocity(ent)
            speed = self._ensure_speed(ent)

            nodes = getattr(path, "noeuds", None)
            if not nodes or prog.index >= len(nodes) - 1:
                self._finish_path(ent, velocity)
                continue

            # prochain nœud à atteindre
            target_node = nodes[prog.index + 1]
            tx, ty = transform.pos
            gx, gy = float(target_node.x), float(target_node.y)

            dx = gx - tx
            dy = gy - ty
            dist = math.hypot(dx, dy)

            # arrivé (snap)
            if dist <= self.arrive_radius:
                transform.pos = (gx, gy)
                gpos.x, gpos.y = int(target_node.x), int(target_node.y)
                prog.index += 1

                # fini
                if prog.index >= len(nodes) - 1:
                    self._finish_path(ent, velocity)
                continue

            # direction vers le nœud
            dirx = dx / dist
            diry = dy / dist

            # vitesse effective (terrain)
            eff_speed = max(self.min_speed, float(speed.base) * float(speed.mult_terrain))

            # si jamais tu utilises encore TerrainEffect ailleurs
            if esper.has_component(ent, TerrainEffect):
                terr = esper.component_for_entity(ent, TerrainEffect)
                eff_speed = terr.apply(eff_speed)

            # déplacement constant => pas de glisse aux virages
            velocity.vx = dirx * eff_speed
            velocity.vy = diry * eff_speed

            step = eff_speed * dt
            if step >= dist:
                # anti-overshoot
                transform.pos = (gx, gy)
                gpos.x, gpos.y = int(target_node.x), int(target_node.y)
                prog.index += 1
                if prog.index >= len(nodes) - 1:
                    self._finish_path(ent, velocity)
                continue

            transform.pos = (tx + velocity.vx * dt, ty + velocity.vy * dt)

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

    def _finish_path(self, ent: int, velocity: Velocity):
        velocity.vx = 0.0
        velocity.vy = 0.0

        # ✅ IMPORTANT : on ne supprime pas Path / PathProgress
        # LaneRouteSystem refait des chemins en vidant path.noeuds
        try:
            if esper.has_component(ent, Path):
                p = esper.component_for_entity(ent, Path)
                p.noeuds = []
        except Exception:
            pass

        try:
            if esper.has_component(ent, PathProgress):
                prog = esper.component_for_entity(ent, PathProgress)
                prog.index = 0
        except Exception:
            pass
