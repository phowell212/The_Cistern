import arcade
import math
import settings as s


class GhostMonster(arcade.Sprite):
    def __init__(self, center_x, center_y, scale):
        super().__init__()

        # Init animation frame arrays
        self.north_idle_frames = []
        self.south_idle_frames = []
        self.hurt_frames = []
        self.death_frames = []
        self.spawn_frames = []

        # Init flags
        self.is_being_hurt = False
        self.is_spawned = False
        self.is_out_of_bounds = False
        self.is_hunting = False
        self.can_hunt = True
        self.direction_lock = False

        # Init counters and values
        self.current_frame = 0
        self.hurt_frame = 0
        self.death_frame = 0
        self.spawn_frame = 0
        self.update_interval = 1 / 10
        self.health = 3
        self.time = 0
        self.bob_frequency = 5
        self.bob_amplitude = 0.3
        self.current_path_position = 0
        self.movement_speed_modifier = 1
        self.direction_lock_timer = 0
        self.direction_lock_stop_time = 20
        self.scale = scale

        # Init directions and position
        self.starting_x = center_x
        self.starting_y = center_y
        self.center_x, self.center_y = center_x, center_y
        self.directions = ["north", "south"]
        self.current_direction = self.directions[1]
        self.load_frames()
        self.debug_path = None
        self.alpha = s.GHOST_ALPHA

    def load_frames(self):
        for i in range(0, 7):
            self.hurt_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_scream-{i}.png"))
        for i in range(0, 10):
            self.death_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_death-{i}.png"))
        self.north_idle_frames.append(arcade.load_texture("assets/enemies/ghost/g_north-0.png"))
        self.south_idle_frames.append(arcade.load_texture("assets/enemies/ghost/g_south-0.png"))
        self.spawn_frames = self.death_frames[::-1]
        self.spawn_frames = self.spawn_frames[1:]

    def update(self):

        # Update the ghost's position
        if not self.is_being_hurt or self.health > 0:
            self.update_animation(1)
            self.center_x += (self.change_x * self.movement_speed_modifier)
            self.center_y += (self.change_y * self.movement_speed_modifier)

            # Make the ghost bob
            self.time += 1 / 60
            self.center_y += math.sin(self.time * self.bob_frequency) * self.bob_amplitude

        # Update the ghost's direction
        if not self.direction_lock:
            if self.change_y > 0:
                self.current_direction = self.directions[0]
                self.direction_lock = True
            else:
                self.current_direction = self.directions[1]
                self.direction_lock = True

        # Time the direction lock
        if self.direction_lock:
            self.direction_lock_timer += 1
            if self.direction_lock_timer > self.direction_lock_stop_time:
                self.direction_lock = False
                self.direction_lock_timer = 0

    def update_animation(self, delta_time: float = 1 / 60):
        self.current_frame += self.update_interval * delta_time

        # If the ghost is spawning in, then play the spawn animation in full
        if not self.is_spawned and self.spawn_frame < len(self.spawn_frames):
            self.texture = self.spawn_frames[self.spawn_frame]
            self.spawn_frame += 1
            if self.spawn_frame == len(self.spawn_frames):
                self.is_spawned = True

        # If the sprite has no health, play that animation then kill it
        elif self.health <= 0 and self.death_frame < len(self.death_frames):
            self.texture = self.death_frames[int(self.death_frame)]
            self.death_frame += 1
        elif self.health <= 0:
            self.death_frame = 0
            s.ghosts_killed += 1
            self.kill()

        # If the monster is being hurt, play the hurt animation
        elif self.is_being_hurt and self.hurt_frame < len(self.hurt_frames) - 1:
            self.hurt_frame += 1 / 3
            self.texture = self.hurt_frames[int(self.hurt_frame)]
        elif self.is_being_hurt:
            self.health -= 1
            self.is_being_hurt = False
            self.hurt_frame = 0

        # If the monster is not being hurt, play the idle animation
        elif self.current_frame < len(self.north_idle_frames):
            if self.current_direction == self.directions[0]:
                self.texture = self.north_idle_frames[int(self.current_frame)]
            else:
                self.texture = self.south_idle_frames[int(self.current_frame)]
        else:
            self.current_frame = 0
