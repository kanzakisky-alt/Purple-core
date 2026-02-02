import pygame

class Weapon:
    def __init__(self, name, length, rotation_map):
        """
        name: String name of weapon
        length: Pixels for the red line (and later sprite scale)
        rotation_map: Dictionary containing lists of angles for each state
        """
        self.name = name
        self.length = length
        self.rotations = rotation_map

    def get_rotation(self, state, frame_index):
        """Returns the specific angle for the current animation frame."""
        # Fallback to [0] if the state (like 'sliding') isn't defined yet
        rot_list = self.rotations.get(state, [0])
        # Use modulo to loop the rotation list if it's shorter than the player animation
        return rot_list[frame_index % len(rot_list)]

# --- Weapon Data Library ---
# You can keep these in the same file or move them to a data.py later

SWORD_DATA = {
    "idle": [-20,-20, -22,-22,-22,-22, -20,-20, -18,-18], # Subtle 'breathing' movement
    "run":  [5, 15, 5, -5, 5, 15, 5, -5], # Swaying with steps
    "jump": [20],
    "fall": [-40]
}

SPEAR_DATA = {
    "idle": [70,70, 72,72,72,72, 70,70,68, 68], # Held mostly upright
    "run":  [45, 50, 45, 40, 45, 50, 45, 40], # Tilted forward for momentum
    "jump": [90],
    "fall": [110]
}

DAGGER_DATA = {
    "idle": [-45], # Tucked away
    "run":  [0, 10, 0, -10], # Quick, short movements
    "jump": [-20],
    "fall": [-20]
}

# --- Initialization ---

def get_all_weapons():
    """Returns a dictionary of all initialized weapon objects."""
    return {
        "sword": Weapon("Iron Sword", 25, SWORD_DATA),
        "spear": Weapon("Long Spear", 45, SPEAR_DATA),
        "dagger": Weapon("Shadow Dagger", 15, DAGGER_DATA),
        # Add your other 2 weapons here later!
    }