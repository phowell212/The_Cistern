import arcade


class DarkFairySpell(arcade.Sprite):
    def __init__(self, center_x, center_y, scale, DarkFairy):
        super().__init__()

        # Init sprite properties
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale
        self.phase = DarkFairy.phase

        # Init animation frames
        self.phase_1_frames = []
        self.current_frame = 0
        self.update_interval = 8
        self.min_spawn_distance = 30
        self.movement_speed_modifier = 2.5
        self.current_path_position = 0
        self.load_frames()
        self.damage = self.phase

        # Pathfinding parameters
        self.path = None

        self.texture = self.phase_1_frames[0]

    def load_frames(self):
        for i in range(0, 12):
            self.phase_1_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_spells/darkfairy_phase1_spell_0-{i}.png"))

    def update(self, delta_time: float = 1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.update_animation(delta_time)

    def update_animation(self, delta_time: float = 1 / 60):
        self.current_frame += delta_time * self.update_interval
        try:
            self.texture = self.phase_1_frames[int(self.current_frame)]
        except IndexError:
            self.kill()
