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
        self.is_hunting = False
        self.is_stuck = False
        self.can_hunt = True

        # Init counters and values
        self.current_frame = 0
        self.hurt_frame = 0
        self.death_frame = 0
        self.spawn_frame = 0
        self.update_interval = 1 / 10
        self.health = 7
        self.time = 0
        self.bob_frequency = 5
        self.bob_amplitude = 0.3
        self.current_path_position = 0
        self.time_since_move = 0
        self.hunt_cooldown = 60
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
        for i in range(0, 1):
            self.north_idle_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_north-{i}.png"))
        for i in range(0, 1):
            self.south_idle_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_south-{i}.png"))
        for i in range(0, 7):
            self.hurt_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_scream-{i}.png"))
        for i in range(0, 10):
            self.death_frames.append(arcade.load_texture(f"assets/enemies/ghost/g_death-{i}.png"))
        self.spawn_frames = self.death_frames[::-1]
        self.spawn_frames = self.spawn_frames[1:]

    def update(self):

        # Update the ghost's position
        if not self.is_being_hurt or self.health > 0:
            self.update_animation(1)
            self.center_x += self.change_x
            self.center_y += self.change_y

            # Make the ghost bob
            self.time += 1 / 60
            self.center_y += math.sin(self.time * self.bob_frequency) * self.bob_amplitude

        else:
            self.update_animation(1 / 2)

        # Update the ghost's direction
        if self.change_y > 0:
            self.current_direction = self.directions[0]
        else:
            self.current_direction = self.directions[1]

    def update_animation(self, delta_time: float = 1 / 60):
        delta_time = 1 / 60
        self.current_frame += self.update_interval * delta_time

        # If the ghost is spawning in, then play the spawn animation in full
        if not self.is_spawned and self.spawn_frame < len(self.spawn_frames):
            self.texture = self.spawn_frames[self.spawn_frame]
            self.spawn_frame += 1
            if self.spawn_frame == len(self.spawn_frames):
                self.is_spawned = True

        # If the sprite has no health, play that animation then kill it
        elif self.health <= 0 and self.death_frame < len(self.death_frames):
            self.texture = self.death_frames[self.death_frame]
            self.death_frame += 1
        elif self.health <= 0:
            self.death_frame = 0
            self.kill()

        # If the monster is being hurt, play the hurt animation
        elif self.is_being_hurt and self.hurt_frame < len(self.hurt_frames) - 1:
            self.hurt_frame += 1
            self.texture = self.hurt_frames[self.hurt_frame]
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
