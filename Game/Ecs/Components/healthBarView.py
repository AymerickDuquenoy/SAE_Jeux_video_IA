from dataclasses import dataclass

@dataclass
class healthBarView:
    """
    Component HealthBarView.
    Définit une liaison avec l'UI pour afficher une barre de vie.
    """
    ui_element_id: int = None  # ID de l'élément UI lié (ex: health bar)

    def __post_init__(self):
        # S'assurer que ui_element_id est défini
        if self.ui_element_id is None:
            raise ValueError("HealthBarView doit avoir un ui_element_id défini.")

    def __str__(self):
        return f"HealthBarView(ui_element_id={self.ui_element_id})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"ui_element_id": self.ui_element_id}