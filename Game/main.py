import sys
import pygame
import esper

from constants import Screen, Colors, Gameplay, Grid
from game.unit_stats import UNIT_STATS

from components import (
    # core
    Position, GridPosition, Sprite, Health, Team, Pyramid,
    # eco/spawn
    Spawner, Wallet, IncomeRate,
    # path/move/combat
    MoveSpeed, PathRequest, Path, PathProgress, Damage, Target,
    # ui + upgrade
    UIInput, UpgradeRequest, PyramidLevel,
)

# Systems (Esper officiel 3.4, Team.id)
from systems.core.economy_system import EconomySystem
from systems.core.spawn_system import SpawnSystem
from systems.core.a_star_system import AStarSystem
from systems.core.path_movement_system import PathMovementSystem
from systems.core.targeting_system import TargetingSystem
from systems.core.combat_system import CombatSystem
from systems.core.death_cleanup_system import DeathCleanupSystem
from systems.core.grid_sync_system import GridSyncSystem
from systems.core.upgrade_system import UpgradeSystem

from systems.ui.ui_system import UISystem
from systems.ui.ui_click_system import UIClickSystem

from systems.render.render_system import RenderSystem
from systems.render.healthbar_system import HealthBarSystem


def main():
    pygame.init()
    screen = pygame.display.set_mode((Screen.WIDTH, Screen.HEIGHT))
    pygame.display.set_caption("Antique War - ECS Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    # Debug imports: Esper officiel doit venir de site-packages
    print("Esper version:", getattr(esper, "__version__", "no __version__"))
    print("Esper file:", esper.__file__)
    print("Python exe:", sys.executable)

    # =========================
    # WORLD (map géante)
    # =========================
    WORLD_WIDTH = 5000
    WORLD_HEIGHT = 2500
    GROUND_Y = WORLD_HEIGHT // 2

    grid_w = WORLD_WIDTH // Grid.TILE_SIZE
    grid_h = WORLD_HEIGHT // Grid.TILE_SIZE

    # =========================
    # UI input singleton
    # =========================
    ui_entity = esper.create_entity()
    esper.add_component(ui_entity, UIInput())

    # =========================
    # Pyramids
    # =========================
    # Player pyramid (team 0)
    player_pyramid = esper.create_entity()
    p_pos = Position(x=200, y=GROUND_Y)
    esper.add_component(player_pyramid, p_pos)
    esper.add_component(player_pyramid, GridPosition(int(p_pos.x // Grid.TILE_SIZE), int(p_pos.y // Grid.TILE_SIZE)))
    esper.add_component(player_pyramid, Sprite(width=80, height=80, color=(180, 120, 80)))
    esper.add_component(player_pyramid, Health(hp=float(Gameplay.PYRAMID_BASE_HP), max_hp=float(Gameplay.PYRAMID_BASE_HP)))
    esper.add_component(player_pyramid, Team(0))
    esper.add_component(player_pyramid, Pyramid())
    esper.add_component(player_pyramid, PyramidLevel(level=0))

    # Enemy pyramid (team 1)
    enemy_pyramid = esper.create_entity()
    e_pos = Position(x=WORLD_WIDTH - 300, y=GROUND_Y)
    esper.add_component(enemy_pyramid, e_pos)
    esper.add_component(enemy_pyramid, GridPosition(int(e_pos.x // Grid.TILE_SIZE), int(e_pos.y // Grid.TILE_SIZE)))
    esper.add_component(enemy_pyramid, Sprite(width=80, height=80, color=(150, 100, 60)))
    esper.add_component(enemy_pyramid, Health(hp=float(Gameplay.PYRAMID_BASE_HP), max_hp=float(Gameplay.PYRAMID_BASE_HP)))
    esper.add_component(enemy_pyramid, Team(1))
    esper.add_component(enemy_pyramid, Pyramid())
    esper.add_component(enemy_pyramid, PyramidLevel(level=0))

    # =========================
    # Controllers (player/enemy)
    # =========================
    player_entity = esper.create_entity()
    esper.add_component(player_entity, Spawner(x=320.0, y=GROUND_Y + 30.0, team_id=0))
    esper.add_component(player_entity, Wallet(amount=0.0))
    esper.add_component(player_entity, IncomeRate(per_second=Gameplay.BASE_INCOME_PER_SEC))
    esper.add_component(player_entity, Team(0))

    enemy_entity = esper.create_entity()
    esper.add_component(enemy_entity, Spawner(x=WORLD_WIDTH - 420.0, y=GROUND_Y + 30.0, team_id=1))
    esper.add_component(enemy_entity, Wallet(amount=0.0))
    esper.add_component(enemy_entity, IncomeRate(per_second=Gameplay.BASE_INCOME_PER_SEC))
    esper.add_component(enemy_entity, Team(1))

    # =========================
    # SYSTEMS PIPELINE
    # =========================
    esper.add_processor(EconomySystem(), priority=100)

    # UI click -> queue spawn / upgrade request
    esper.add_processor(UIClickSystem(screen, player_entity=player_entity), priority=90)
    esper.add_processor(UpgradeSystem(), priority=85)

    esper.add_processor(SpawnSystem(), priority=80)
    esper.add_processor(AStarSystem(grid_w, grid_h, obstacles=set()), priority=70)

    esper.add_processor(TargetingSystem(), priority=60)
    esper.add_processor(CombatSystem(), priority=50)
    esper.add_processor(DeathCleanupSystem(), priority=40)

    esper.add_processor(PathMovementSystem(), priority=30)
    esper.add_processor(GridSyncSystem(), priority=20)

    render = RenderSystem(screen, world_w=WORLD_WIDTH, world_h=WORLD_HEIGHT, camera_speed=700.0)
    # Start camera near player pyramid
    render.cam_x = max(0, min(p_pos.x - Screen.WIDTH / 2, WORLD_WIDTH - Screen.WIDTH))
    render.cam_y = max(0, min(p_pos.y - Screen.HEIGHT / 2, WORLD_HEIGHT - Screen.HEIGHT))
    esper.add_processor(render, priority=10)

    esper.add_processor(HealthBarSystem(screen), priority=5)
    esper.add_processor(UISystem(screen, font, player_entity=player_entity), priority=0)

    # =========================
    # LOOP
    # =========================
    running = True
    while running:
        dt = clock.tick(Screen.FPS) / 1000.0

        # Fill UIInput singleton
        ui = esper.component_for_entity(ui_entity, UIInput)
        ui.mouse_pos = pygame.mouse.get_pos()
        ui.mouse_clicks.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ui.mouse_clicks.append(event.pos)

            # (optionnel) raccourcis clavier pour test rapide
            if event.type == pygame.KEYDOWN:
                spawner = esper.component_for_entity(player_entity, Spawner)
                wallet = esper.component_for_entity(player_entity, Wallet)

                def buy(unit_type: str):
                    cost = UNIT_STATS[unit_type]["cost"]
                    if wallet.amount >= cost:
                        wallet.amount -= cost
                        spawner.queue.append(unit_type)
                        print(f"[KEY] Bought {unit_type} for {cost} 𓍯 (wallet={wallet.amount:.1f})")

                if event.key == pygame.K_1:
                    buy("momie")
                elif event.key == pygame.K_2:
                    buy("dromadaire")
                elif event.key == pygame.K_3:
                    buy("sphinx")
                elif event.key == pygame.K_u:
                    if not esper.has_component(player_entity, UpgradeRequest):
                        esper.add_component(player_entity, UpgradeRequest())

        screen.fill(Colors.BG)
        esper.process(dt)

        # Debug caption wallet
        pw = esper.component_for_entity(player_entity, Wallet).amount
        ew = esper.component_for_entity(enemy_entity, Wallet).amount
        pygame.display.set_caption(f"Antique War - Player: {pw:.1f} 𓍯 | Enemy: {ew:.1f} 𓍯")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    print("Esper file:", esper.__file__)
    main()
