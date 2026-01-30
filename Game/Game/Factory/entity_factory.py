# Game/Factory/entity_factory.py
from __future__ import annotations

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.pyramidLevel import PyramidLevel


class EntityFactory:
    # Initialise la factory avec le monde ECS, taille des tuiles et configuration de balance
    def __init__(self, world, *, tile_size: int = 32, balance: dict | None = None):
        self.world = world
        self.tile_size = int(tile_size)
        self.balance = balance or {}

    # Récupère une valeur dans la configuration de balance avec navigation par clés
    def _get(self, *keys, default=None):
        d = self.balance
        for k in keys:
            if not isinstance(d, dict) or k not in d:
                return default
            d = d[k]
        return d

    # Récupère la constante k pour le calcul du coût (C = k*P)
    def _get_k(self) -> float:
        # k pour C = kP (on tente plusieurs emplacements possibles)
        k = self._get("sae", "k_cost_per_power", default=None)
        if k is None:
            k = self._get("constraints", "k_cost_per_power", default=None)
        if k is None:
            k = self._get("constraints", "k", default=None)
        return float(k) if k is not None else 10.0

    # Récupère la constante pour V + B = constante
    def _get_v_plus_b(self) -> float:
        # constante pour V + B = cste
        vb = self._get("sae", "v_plus_b", default=None)
        if vb is None:
            vb = self._get("constraints", "v_plus_b", default=None)
        if vb is None:
            vb = self._get("constraints", "v_plus_b_const", default=None)
        return float(vb) if vb is not None else 100.0

    # Convertit la vitesse SAÉ (0-100) en vitesse de déplacement jouable (cases/seconde)
    def _v_to_move_speed(self, v_value: float) -> float:
        """
        Convertit le V de la SAE (ex: 0..100) en vitesse de déplacement (cases / seconde).
        On garde V dans UnitStats pour l'affichage/contrainte, mais Speed.base doit être "jouable".
        """
        vb = self._get_v_plus_b()
        vb = vb if vb > 0 else 100.0

        MOVE_SPEED_MAX = 4.0  # 100 de V => 4 cases/s (ajustable)
        ratio = max(0.0, min(1.0, float(v_value) / vb))
        speed = ratio * MOVE_SPEED_MAX

        # évite une vitesse trop lente
        return max(0.6, speed)

    # Calcule les statistiques d'une unité selon les contraintes SAÉ
    def compute_unit_stats(self, unit_key: str) -> UnitStats:
        unit_key = str(unit_key).upper().strip()
        data = self._get("units", unit_key, default={})
        if not isinstance(data, dict):
            data = {}

        # 2 paramètres "libres" (SAÉ) : on prend vitesse + puissance
        # Le reste est dérivé par contraintes.
        speed = float(data.get("speed", 70.0))
        power = float(data.get("power", 10.0))

        k = self._get_k()
        vb = self._get_v_plus_b()

        # Contraintes SAÉ :
        cost = k * power
        armor = max(0.0, vb - speed)  # B (blindage)

        return UnitStats(speed=speed, power=power, armor=armor, cost=cost)

    # Crée une entité pyramide avec position, équipe, santé et niveau
    def create_pyramid(self, *, team_id: int, grid_pos: tuple[int, int]) -> int:
        gx, gy = int(grid_pos[0]), int(grid_pos[1])

        # P0 : blindage de la base = points de vie
        # On met +1 pour coller strictement à n*P > B (si B est entier).
        hp_base = int(self._get("pyramid", "hp_base", default=500))
        hp_max = hp_base + 1
        hp = hp_max

        components = [
            GridPosition(gx, gy),
            Transform(pos=(float(gx), float(gy))),  # coords grille
            Team(int(team_id)),
            Health(hp_max=hp_max, hp=hp),
            PyramidLevel(level=1),  # Niveau initial de la pyramide
        ]

        # Wallet côté joueur (team 1)
        if int(team_id) == 1:
            start_money = float(self._get("economy", "starting_money", default=100.0))
            components.append(Wallet(solde=start_money))

        return self.world.create_entity(*components)

    # Crée une entité unité avec tous ses composants (stats, santé, vitesse, etc.)
    def create_unit(self, unit_key: str, *, team_id: int, grid_pos: tuple[int, int]) -> int:
        gx, gy = int(grid_pos[0]), int(grid_pos[1])

        stats = self.compute_unit_stats(unit_key)

        # P0 (SAÉ strict) :
        # Blindage B = points de vie.
        # Destruction quand n*P > B -> équivalent à HP=B+1 et dégâts=P par coup au but.
        b = int(round(float(stats.armor)))
        hp_max = b + 1

        move_speed = self._v_to_move_speed(stats.speed)

        return self.world.create_entity(
            GridPosition(gx, gy),
            Transform(pos=(float(gx), float(gy))),  # coords grille
            Team(int(team_id)),
            Health(hp_max=int(hp_max), hp=int(hp_max)),
            UnitStats(speed=float(stats.speed), power=float(stats.power), armor=float(stats.armor), cost=float(stats.cost)),
            Speed(base=float(move_speed), mult_terrain=1.0),
        )