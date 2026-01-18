import esper
from components import Position, Team, Health, Damage, Pyramid, Target


class TargetingSystem(esper.Processor):
    def process(self, dt: float):

        units = []
        for e, (pos, hp, team) in esper.get_components(Position, Health, Team):
            if hp.hp <= 0:
                continue
            if esper.has_component(e, Pyramid):
                continue
            units.append((e, pos, team))

        pyramids = []
        for p, (pos, hp, team, _pyr) in esper.get_components(Position, Health, Team, Pyramid):
            if hp.hp <= 0:
                continue
            pyramids.append((p, pos, team))

        for ent, (pos, team, hp, _dmg) in esper.get_components(Position, Team, Health, Damage):
            if hp.hp <= 0 or esper.has_component(ent, Pyramid):
                continue

            best = None
            best_d2 = 1e30

            for u_ent, u_pos, u_team in units:
                if u_ent == ent:
                    continue
                if u_team.id == team.id:
                    continue
                dx = u_pos.x - pos.x
                dy = u_pos.y - pos.y
                d2 = dx*dx + dy*dy
                if d2 < best_d2:
                    best_d2 = d2
                    best = u_ent

            if best is None:
                for p_ent, p_pos, p_team in pyramids:
                    if p_team.id == team.id:
                        continue
                    dx = p_pos.x - pos.x
                    dy = p_pos.y - pos.y
                    d2 = dx*dx + dy*dy
                    if d2 < best_d2:
                        best_d2 = d2
                        best = p_ent

            if esper.has_component(ent, Target):
                esper.component_for_entity(ent, Target).entity = best
            else:
                esper.add_component(ent, Target(entity=best))
