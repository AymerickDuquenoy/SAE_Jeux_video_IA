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
    Suit un Path calculé par A* et déplace l'entité vers le goal.

    - Transform.pos est en "coord grille" (float)
    - Speed.base est une vitesse en cases / seconde
    - Anti-overshoot : si on dépasse le prochain noeud, on snap dessus.
    """

    def __init__(
        self,
        *,
        max_accel: float = 10.0,
        arrive_radius: float = 0.15,
        min_speed: float = 0.0
    ):
        super().__init__()
        self.max_accel = float(max_accel)
        self.arrive_radius = float(arrive_radius)
        self.min_speed = float(min_speed)

    def process(self, dt: float):
        if dt <= 0:
            return

        for ent, (gpos, path, prog) in esper.get_components(GridPosition, Path, PathProgress):
            transform = self._ensure_transform(ent, gpos)
            velocity = self._ensure_velocity(ent)
            speed = self._ensure_speed(ent)

            nodes = path.noeuds
            if not nodes or prog.index >= len(nodes) - 1:
                self._finish_path(ent, velocity)
                continue

            target_node = nodes[prog.index + 1]
            tx, ty = transform.pos
            gx, gy = float(target_node.x), float(target_node.y)

            dx = gx - tx
            dy = gy - ty
            dist = math.hypot(dx, dy)

            if dist <= self.arrive_radius:
                transform.pos = (gx, gy)
                gpos.x, gpos.y = target_node.x, target_node.y
                prog.index += 1
                if prog.index >= len(nodes) - 1:
                    self._finish_path(ent, velocity)
                continue

            dirx = dx / dist
            diry = dy / dist

            eff_speed = max(self.min_speed, speed.base * speed.mult_terrain)
            if esper.has_component(ent, TerrainEffect):
                terr = esper.component_for_entity(ent, TerrainEffect)
                eff_speed = terr.apply(eff_speed)

            braking_dist = (eff_speed ** 2) / (2 * self.max_accel) if self.max_accel > 0 else 0.0
            desired_speed = eff_speed
            if braking_dist > 0 and dist < braking_dist:
                desired_speed = eff_speed * (dist / braking_dist)

            desired_vx = dirx * desired_speed
            desired_vy = diry * desired_speed

            dvx = desired_vx - velocity.vx
            dvy = desired_vy - velocity.vy
            dv_len = math.hypot(dvx, dvy)

            max_dv = self.max_accel * dt
            if dv_len > max_dv and dv_len > 1e-8:
                scale = max_dv / dv_len
                dvx *= scale
                dvy *= scale

            velocity.vx += dvx
            velocity.vy += dvy

            # ---- anti-overshoot ----
            step = math.hypot(velocity.vx, velocity.vy) * dt
            if step >= dist:
                transform.pos = (gx, gy)
                gpos.x, gpos.y = target_node.x, target_node.y
                prog.index += 1
                if prog.index >= len(nodes) - 1:
                    self._finish_path(ent, velocity)
                continue
            # ------------------------

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
        if esper.has_component(ent, Path):
            esper.remove_component(ent, Path)
        if esper.has_component(ent, PathProgress):
            esper.remove_component(ent, PathProgress)
