import arcade
import settings as s


class DarkFairy(arcade.Sprite):
    def __init__(self, center_x, center_y, scale):
        super().__init__()

        # Init animation frame arrays
        self.phase_1_idle_frames = []
        self.phase_1_hurt_frames = []
        self.phase_1_cast_frames = []
        self.transform_frames = []
        self.phase_2_idle_frames = []
        self.phase_2_hurt_frames = []
        self.phase_2_cast_frames = []
        self.death_frames = []

        # Init the boss variables
        self.health = s.BOSS_HEALTH
        self.is_casting = False
        self.is_being_hurt = False
        self.is_transforming = False
        self.is_dying = False
        self.phase = 1
        self.min_spawn_distance = 150
        self.movement_speed_modifier = 1
        self.current_frame = 0
        self.casting_frame = 0
        self.hurt_frame = 0
        self.update_interval = 1 / 10

        # Init the class parameters
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale

        self.load_frames()

    def load_frames(self):
        for i in range(0, 7):
            self.phase_1_cast_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase1_castspell_{i}.png"))
        for i in range(0, 2):
            self.phase_1_hurt_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase1_hurt_{i}.png"))
        for i in range(0, 7):
            self.phase_1_idle_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase1_idle{i}.png"))
        for i in range(0, 10):
            self.transform_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_transformation_into_phase2_0{i}.png"))
        for i in range(0, 6):
            self.transform_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_transformation_into_phase2_1{i}.png"))
        for i in range(0, 4):
            self.phase_2_cast_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase2_castspell_{i}.png"))
        for i in range(0, 3):
            self.phase_2_hurt_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase2_hurt_{i}.png"))
        for i in range(0, 2):
            self.phase_2_idle_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase2_idle_{i}.png"))
        for i in range(0, 10):
            self.death_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase2_death_0{i}.png"))
        for i in range(0, 4):
            self.death_frames.append(arcade.load_texture(
                f"assets/enemies/darkfairy_new/darkfairy_phase2_death_1{i}.png"))

        self.phase_1_idle_frames.extend(self.phase_1_idle_frames[::-1])
        self.phase_2_idle_frames.extend(self.phase_2_idle_frames[::-1])
        self.phase_1_cast_frames.extend(self.phase_1_cast_frames[::-1])
        self.phase_2_cast_frames.extend(self.phase_2_cast_frames[::-1])

    def update_animation(self, delta_time: float = 1 / 60):
        delta_time = 1.25
        self.current_frame += self.update_interval * delta_time

        if self.phase == 1:

            # Handle the transformation
            if self.health <= 0:
                if not self.is_transforming and self.current_frame != 0:
                    self.current_frame = 0
                    self.is_transforming = True
                elif not self.is_transforming:
                    self.is_transforming = True
                if self.is_transforming:
                    try:
                        self.texture = self.transform_frames[int(self.current_frame)]
                    except IndexError:
                        self.is_transforming = False
                        self.health = s.BOSS_HEALTH
                        self.current_frame = 0
                        self.phase = 2

            elif self.is_casting and self.casting_frame < len(self.phase_1_cast_frames) and not self.is_being_hurt:
                self.casting_frame += 1 / 3
                try:
                    self.texture = self.phase_1_cast_frames[int(self.casting_frame)]
                except IndexError:
                    self.is_casting = False
                    self.casting_frame = 0

            elif self.is_being_hurt and self.hurt_frame < len(self.phase_1_hurt_frames):
                self.hurt_frame += 1 / 3
                try:
                    self.texture = self.phase_1_hurt_frames[int(self.hurt_frame)]
                except IndexError:
                    self.is_being_hurt = False
                    self.hurt_frame = 0

            else:
                try:
                    self.texture = self.phase_1_idle_frames[int(self.current_frame)]
                except IndexError:
                    self.current_frame = 0
                    self.texture = self.phase_1_idle_frames[int(self.current_frame)]

        elif self.phase == 2:

            # Handle the death
            if self.health <= 0:
                if not self.is_dying and self.current_frame != 0:
                    self.current_frame = 0
                    self.is_dying = True
                elif not self.is_dying:
                    self.is_dying = True
                if self.is_dying:
                    try:
                        self.texture = self.death_frames[int(self.current_frame)]
                    except IndexError:
                        self.kill()
                        s.bosses_to_spawn += 1

            elif self.is_casting and self.casting_frame < len(self.phase_2_cast_frames):
                self.casting_frame += 1 / 3
                try:
                    self.texture = self.phase_2_cast_frames[int(self.casting_frame)]
                except IndexError:
                    self.is_casting = False
                    self.casting_frame = 0

            elif self.is_being_hurt and self.hurt_frame < len(self.phase_2_hurt_frames):
                self.hurt_frame += 1 / 3
                try:
                    self.texture = self.phase_2_hurt_frames[int(self.hurt_frame)]
                except IndexError:
                    self.is_being_hurt = False
                    self.hurt_frame = 0

            else:
                if self.current_frame < 1:
                    self.texture = self.phase_2_idle_frames[0]
                elif self.current_frame < 2:
                    self.texture = self.phase_2_idle_frames[1]
                else:
                    self.current_frame = 0
                    self.texture = self.phase_2_idle_frames[0]

    def update(self):
        self.update_animation()
        if self.health >= 0:
            self.center_x += self.change_x
            self.center_y += self.change_y
