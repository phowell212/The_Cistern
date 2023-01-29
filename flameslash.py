import arcade
import settings as s


class FlameSlash(arcade.Sprite):
    def __init__(self, player):
        super().__init__()

        # Set the starting position and direction of the projectile based on the player's position and facing direction
        self.center_x = player.center_x
        self.center_y = player.center_y
        self.direction = player.current_direction
        self.scale = s.FLAME_SLASH_SCALING
        self.player_copy = player

        self.is_hitting_wall = False
        self.update_interval = 1 / 20
        self.elapsed_time = 0
        self.offset = 20
        self.alpha = 0

        # Set the first texture based on the sprite's direction
        if self.direction == "northwest":
            self.texture = arcade.load_texture("assets/flameslash/flameslash_northwest-0.png")
            self.center_x -= self.offset
            self.center_y += self.offset
        elif self.direction == "southwest":
            self.texture = arcade.load_texture("assets/flameslash/flameslash_southwest-0.png")
            self.center_x -= self.offset
            self.center_y -= self.offset
        elif self.direction == "northeast":
            self.texture = arcade.load_texture("assets/flameslash/flameslash_northeast-0.png")
            self.center_x += self.offset
            self.center_y += self.offset
        elif self.direction == "southeast":
            self.texture = arcade.load_texture("assets/flameslash/flameslash_southeast-0.png")
            self.center_x += self.offset
            self.center_y -= self.offset
        elif self.direction == "north":
            self.texture = arcade.load_texture("assets/flameslash/flameslash_north-0.png")
            self.center_y += self.offset
        elif self.direction == "south":
            self.texture = arcade.load_texture("assets/flameslash/flameslash_south-0.png")
            self.center_y -= self.offset
        elif self.direction == "east":
            self.texture = arcade.load_texture("assets/flameslash/flameslash-east-0.png")
            self.center_x += self.offset
        elif self.direction == "west":
            self.texture = arcade.load_texture("assets/flameslash/flameslash-west-0.png")
            self.center_x -= self.offset

        # Load the animation frames
        self.northwest_frames = []
        self.southwest_frames = []
        self.northeast_frames = []
        self.southeast_frames = []
        self.north_frames = []
        self.south_frames = []
        self.east_frames = []
        self.west_frames = []
        self.current_frame = 0
        self.load_frames()

    def load_frames(self):

        # I named the northeast and northwest frames wrong, shh
        for i in range(1, 18):
            self.northeast_frames.append(arcade.load_texture(f"assets/flameslash/flameslash_northwest-{i}.png"))
            self.southwest_frames.append(arcade.load_texture(f"assets/flameslash/flameslash_southwest-{i}.png"))
            self.northwest_frames.append(arcade.load_texture(f"assets/flameslash/flameslash_northeast-{i}.png"))
            self.southeast_frames.append(arcade.load_texture(f"assets/flameslash/flameslash_southeast-{i}.png"))
            self.north_frames.append(arcade.load_texture(f"assets/flameslash/flameslash_north-{i}.png"))
            self.south_frames.append(arcade.load_texture(f"assets/flameslash/flameslash_south-{i}.png"))
            self.east_frames.append(arcade.load_texture(f"assets/flameslash/flameslash-east-{i}.png"))
            self.west_frames.append(arcade.load_texture(f"assets/flameslash/flameslash-west-{i}.png"))

    def update(self):
        if not self.is_hitting_wall:
            if self.direction == "northwest":
                self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED
                self.center_y += s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "northwest":
                    self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED
                    self.center_y += s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "northwest":
                    self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED * 2
                    self.center_y += s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "southwest":
                self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED
                self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "southwest":
                    self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED
                    self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "southwest":
                    self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED * 2
                    self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "northeast":
                self.center_x += s.FLAMESLASH_PROJECTILE_SPEED
                self.center_y += s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "northeast":
                    self.center_x += s.FLAMESLASH_PROJECTILE_SPEED
                    self.center_y += s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "northeast":
                    self.center_x += s.FLAMESLASH_PROJECTILE_SPEED * 2
                    self.center_y += s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "southeast":
                self.center_x += s.FLAMESLASH_PROJECTILE_SPEED
                self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "southeast":
                    self.center_x += s.FLAMESLASH_PROJECTILE_SPEED
                    self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "southeast":
                    self.center_x += s.FLAMESLASH_PROJECTILE_SPEED * 2
                    self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "north":
                self.center_y += s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "north":
                    self.center_y += s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "north":
                    self.center_y += s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "south":
                self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "south":
                    self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "south":
                    self.center_y -= s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "east":
                self.center_x += s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "east":
                    self.center_x += s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "east":
                    self.center_x += s.FLAMESLASH_PROJECTILE_SPEED * 2
            elif self.direction == "west":
                self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED
                if self.player_copy.is_walking and self.player_copy.current_direction == "west":
                    self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED
                elif self.player_copy.is_running and self.player_copy.current_direction == "west":
                    self.center_x -= s.FLAMESLASH_PROJECTILE_SPEED * 2

    def update_animation(self, delta_time: float = 1/60):
        self.current_frame += 1

        # Have the flameslash fade in and out
        if self.current_frame < 4:
            self.alpha = 255 * (self.current_frame / 5)
        elif 4 < self.current_frame < 20:
            self.alpha = 255
        else:
            self.alpha = 255 / (5 - (self.current_frame - 20))

        if self.direction == "northwest" and self.current_frame < len(self.northwest_frames):
            self.texture = self.northwest_frames[int(self.current_frame)]
        elif self.direction == "southwest" and self.current_frame < len(self.southwest_frames):
            self.texture = self.southwest_frames[int(self.current_frame)]
        elif self.direction == "northeast" and self.current_frame < len(self.northeast_frames):
            self.texture = self.northeast_frames[int(self.current_frame)]
        elif self.direction == "southeast" and self.current_frame < len(self.southeast_frames):
            self.texture = self.southeast_frames[int(self.current_frame)]
        elif self.direction == "north" and self.current_frame < len(self.north_frames):
            self.texture = self.north_frames[int(self.current_frame)]
        elif self.direction == "south" and self.current_frame < len(self.south_frames):
            self.texture = self.south_frames[int(self.current_frame)]
        elif self.direction == "east" and self.current_frame < len(self.east_frames):
            self.texture = self.east_frames[int(self.current_frame)]
        elif self.direction == "west" and self.current_frame < len(self.west_frames):
            self.texture = self.west_frames[int(self.current_frame)]
        else:
            self.kill()
