import arcade

'''
ANIMATION INFO:

NORTH:
0 - 5: Idle
6 - 11: Walking
12 - 17: Running
18 - 21: Run Stop
22 - 43: Slash
44 - 53: Roll
54 - 57: Dash
58 - 67: Dash Stab
68 - 81: Dash Slash
82 - 87: Bow Basic Aim
88 - 92: Bow Basic Shoot
93 - 97: Bow Charge Aim
98 - 102: Bow Charge Hold

NORTHEAST AND NORTHWEST:
0 - 5: Idle
6 - 11: Walking
12 - 17: Running
18 - 21: Run Stop
22 - 31: Roll
32 - 41: Dash
42 - 55: Dash Slash
56 - 77: Slash
78 - 83: Bow Basic Aim
84 - 88: Bow Basic Shoot
89 - 93: Bow Charge Aim
94 - 98: Bow Charge Shoot

EAST AND WEST:
0 - 5: Idle
6 - 11: Walking
12 - 17: Running
18 - 21: Run Stop
22 - 31: Roll
32 - 53: Slash
54 - 67: X Slash
68 - 71: Dash
72 - 81: Dash Stab
82 - 84: Bow Basic Aim
85 - 91: Bow Basic Shoot
92 - 96: Bow Charge Aim
97 - 101: Bow Charge Hold

SOUTHEAST AND SOUTHWEST:
0 - 5: Idle
6 - 11: Walking
12 - 17: Running
18 - 21: Run Stop
22 - 25: Dash
26 - 35: Roll
36 - 45: Dash Stab
46 - 59: Dash Slash
60 - 82: Slash
83 - 88: Bow Basic Aim
89 - 93: Bow Basic Shoot
94 - 98: Bow Charge Aim
99 - 103: Bow Charge Hold

SOUTH:
0 - 5: Idle
6 - 11: Walking
12 - 17: Running
18 - 21: Run Stop
22 - 43: Slash
44 - 53: Roll
54 - 57: Dash
58 - 67: Dash Stab
68 - 81: Dash Slash
82 - 87: Bow Basic Aim
88 - 92: Bow Basic Shoot
93 - 97: Bow Charge Aim
98 - 102: Bow Charge Hold
'''


class Player(arcade.Sprite):
    def __init__(self, center_x, center_y, scale):
        super().__init__()

        # Init the sprite
        self.is_walking = False
        self.is_running = False
        self.is_slashing = False
        self.just_stopped_running = False
        self.run_stop_animation_frame = 22
        self.current_frame = 0
        self.elapsed_time = 0
        self.directions = ["north", "west", "south", "east", "northwest", "northeast", "southwest", "southeast"]
        self.current_direction = self.directions[2]
        self.update_interval = 1 / 10
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale
        self.texture = arcade.load_texture("assets/player/south-0.png")

        # Load the frame arrays
        self.north_idle_frames = []
        self.north_walking_frames = []
        self.north_running_frames = []
        self.north_run_stop_frames = []
        self.north_slash_frames = []
        self.north_roll_frames = []
        self.north_dash_frames = []
        self.north_dash_stab_frames = []
        self.north_dash_slash_frames = []
        self.west_idle_frames = []
        self.west_walking_frames = []
        self.west_running_frames = []
        self.west_run_stop_frames = []
        self.west_roll_frames = []
        self.west_slash_frames = []
        self.west_x_slash_frames = []
        self.west_dash_frames = []
        self.west_dash_stab_frames = []
        self.south_idle_frames = []
        self.south_walking_frames = []
        self.south_running_frames = []
        self.south_run_stop_frames = []
        self.south_slash_frames = []
        self.south_roll_frames = []
        self.south_dash_frames = []
        self.south_dash_stab_frames = []
        self.south_dash_slash_frames = []
        self.east_idle_frames = []
        self.east_walking_frames = []
        self.east_running_frames = []
        self.east_run_stop_frames = []
        self.east_roll_frames = []
        self.east_slash_frames = []
        self.east_x_slash_frames = []
        self.east_dash_frames = []
        self.east_dash_stab_frames = []
        self.northeast_idle_frames = []
        self.northeast_walking_frames = []
        self.northeast_running_frames = []
        self.northeast_run_stop_frames = []
        self.northeast_roll_frames = []
        self.northeast_dash_frames = []
        self.northeast_dash_slash_frames = []
        self.northeast_slash_frames = []
        self.northwest_idle_frames = []
        self.northwest_walking_frames = []
        self.northwest_running_frames = []
        self.northwest_run_stop_frames = []
        self.northwest_roll_frames = []
        self.northwest_dash_frames = []
        self.northwest_dash_slash_frames = []
        self.northwest_slash_frames = []
        self.southeast_idle_frames = []
        self.southeast_walking_frames = []
        self.southeast_running_frames = []
        self.southeast_run_stop_frames = []
        self.southeast_dash_frames = []
        self.southeast_roll_frames = []
        self.southeast_dash_stab_frames = []
        self.southeast_dash_slash_frames = []
        self.southeast_slash_frames = []
        self.southwest_idle_frames = []
        self.southwest_walking_frames = []
        self.southwest_running_frames = []
        self.southwest_run_stop_frames = []
        self.southwest_dash_frames = []
        self.southwest_roll_frames = []
        self.southwest_dash_stab_frames = []
        self.southwest_dash_slash_frames = []
        self.southwest_slash_frames = []

        # Load the frames
        self.load_frames()

        # Other stuff
        self.c_key_timer = 0.0

    def load_frames(self):

        # Load the north facing frames
        for i in range(0, 5):
            self.north_idle_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(6, 11):
            self.north_walking_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(12, 17):
            self.north_running_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(18, 21):
            self.north_run_stop_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(22, 43):
            self.north_slash_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(44, 53):
            self.north_roll_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(54, 57):
            self.north_dash_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(58, 67):
            self.north_dash_stab_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))
        for i in range(68, 81):
            self.north_dash_slash_frames.append(arcade.load_texture(f"assets/player/north-{i}.png"))

        # Load the west facing frames
        for i in range(0, 5):
            self.west_idle_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(6, 11):
            self.west_walking_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(12, 17):
            self.west_running_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(18, 21):
            self.west_run_stop_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(22, 31):
            self.west_roll_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(32, 53):
            self.west_slash_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(54, 67):
            self.west_x_slash_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(68, 71):
            self.west_dash_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))
        for i in range(72, 81):
            self.west_dash_stab_frames.append(arcade.load_texture(f"assets/player/west-{i}.png"))

        # Load the south facing frames
        for i in range(0, 5):
            self.south_idle_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(6, 11):
            self.south_walking_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(12, 17):
            self.south_running_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(18, 21):
            self.south_run_stop_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(22, 43):
            self.south_slash_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(44, 53):
            self.south_roll_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(54, 57):
            self.south_dash_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(58, 67):
            self.south_dash_stab_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))
        for i in range(68, 81):
            self.south_dash_slash_frames.append(arcade.load_texture(f"assets/player/south-{i}.png"))

        # Load the east facing frames
        for i in range(0, 5):
            self.east_idle_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(6, 11):
            self.east_walking_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(12, 17):
            self.east_running_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(18, 21):
            self.east_run_stop_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(22, 31):
            self.east_roll_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(32, 53):
            self.east_slash_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(54, 67):
            self.east_x_slash_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(68, 71):
            self.east_dash_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))
        for i in range(72, 81):
            self.east_dash_stab_frames.append(arcade.load_texture(f"assets/player/east-{i}.png"))

        # Load the northeast facing frames
        for i in range(0, 5):
            self.northeast_idle_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(6, 11):
            self.northeast_walking_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(12, 17):
            self.northeast_running_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(18, 21):
            self.northeast_run_stop_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(22, 31):
            self.northeast_roll_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(32, 41):
            self.northeast_dash_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(42, 55):
            self.northeast_dash_slash_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))
        for i in range(56, 77):
            self.northeast_slash_frames.append(arcade.load_texture(f"assets/player/northeast-{i}.png"))

        # Load the northwest facing frames
        for i in range(0, 5):
            self.northwest_idle_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(6, 11):
            self.northwest_walking_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(12, 17):
            self.northwest_running_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(18, 21):
            self.northwest_run_stop_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(22, 31):
            self.northwest_roll_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(32, 41):
            self.northwest_dash_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(42, 55):
            self.northwest_dash_slash_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))
        for i in range(56, 77):
            self.northwest_slash_frames.append(arcade.load_texture(f"assets/player/northwest-{i}.png"))

        # Load the southeast facing frames
        for i in range(0, 5):
            self.southeast_idle_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(6, 11):
            self.southeast_walking_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(12, 17):
            self.southeast_running_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(18, 21):
            self.southeast_run_stop_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(22, 25):
            self.southeast_dash_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(26, 35):
            self.southeast_roll_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(36, 45):
            self.southeast_dash_stab_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(46, 59):
            self.southeast_dash_slash_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))
        for i in range(60, 82):
            self.southeast_slash_frames.append(arcade.load_texture(f"assets/player/southeast-{i}.png"))

        # Load the southwest facing frames
        for i in range(0, 5):
            self.southwest_idle_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(6, 11):
            self.southwest_walking_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(12, 17):
            self.southwest_running_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(18, 21):
            self.southwest_run_stop_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(22, 25):
            self.southwest_dash_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(26, 35):
            self.southwest_roll_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(36, 45):
            self.southwest_dash_stab_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(46, 59):
            self.southwest_dash_slash_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))
        for i in range(60, 82):
            self.southwest_slash_frames.append(arcade.load_texture(f"assets/player/southwest-{i}.png"))

    def update_animation(self, delta_time: float = 1 / 10):
        # Update the animation frame
        self.elapsed_time += delta_time
        if self.elapsed_time > self.update_interval:
            self.elapsed_time = 0
            self.current_frame += 1

        # Update the sprite texture
        if self.just_stopped_running is True and self.run_stop_animation_frame >= 21:
            self.run_stop_animation_frame = 18
            self.just_stopped_running = False
            self.is_running = False

        if self.is_slashing:
            if self.current_direction == self.directions[0] and \
                    self.current_frame < self.north_slash_frames.__len__():
                self.texture = self.north_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[1] and \
                    self.current_frame < self.west_slash_frames.__len__():
                self.texture = self.west_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[2] and \
                    self.current_frame < self.south_slash_frames.__len__():
                self.texture = self.south_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[3] and \
                    self.current_frame < self.east_slash_frames.__len__():
                self.texture = self.east_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[4] and \
                    self.current_frame < self.northwest_slash_frames.__len__():
                self.texture = self.northwest_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[5] and \
                    self.current_frame < self.northeast_slash_frames.__len__():
                self.texture = self.northeast_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[6] and \
                    self.current_frame < self.southwest_slash_frames.__len__():
                self.texture = self.southwest_slash_frames[self.current_frame]
            elif self.current_direction == self.directions[7] and \
                    self.current_frame < self.southeast_slash_frames.__len__():
                self.texture = self.southeast_slash_frames[self.current_frame]
            else:
                self.is_slashing = False
                self.current_frame = 0
                self.c_key_timer = 0

        # Run stop has to have a different animation frame counter because it is triggered
        elif self.run_stop_animation_frame < 21:
            if self.current_direction == self.directions[0]:
                self.texture = self.north_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[1]:
                self.texture = self.west_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[2]:
                self.texture = self.south_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[3]:
                self.texture = self.east_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[4]:
                self.texture = self.northwest_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[5]:
                self.texture = self.northeast_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[6]:
                self.texture = self.southwest_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1
            elif self.current_direction == self.directions[7]:
                self.texture = self.southeast_run_stop_frames[self.run_stop_animation_frame - 18]
                self.run_stop_animation_frame += 1

        elif self.is_running:
            if self.current_direction == self.directions[0] and \
                    self.current_frame < self.north_running_frames.__len__():
                self.texture = self.north_running_frames[self.current_frame]
            elif self.current_direction == self.directions[1] and \
                    self.current_frame < self.west_running_frames.__len__():
                self.texture = self.west_running_frames[self.current_frame]
            elif self.current_direction == self.directions[2] and \
                    self.current_frame < self.south_running_frames.__len__():
                self.texture = self.south_running_frames[self.current_frame]
            elif self.current_direction == self.directions[3] and \
                    self.current_frame < self.east_running_frames.__len__():
                self.texture = self.east_running_frames[self.current_frame]
            elif self.current_direction == self.directions[4] and \
                    self.current_frame < self.northwest_running_frames.__len__():
                self.texture = self.northwest_running_frames[self.current_frame]
            elif self.current_direction == self.directions[5] and \
                    self.current_frame < self.northeast_running_frames.__len__():
                self.texture = self.northeast_running_frames[self.current_frame]
            elif self.current_direction == self.directions[6] and \
                    self.current_frame < self.southwest_running_frames.__len__():
                self.texture = self.southwest_running_frames[self.current_frame]
            elif self.current_direction == self.directions[7] and \
                    self.current_frame < self.southeast_running_frames.__len__():
                self.texture = self.southeast_running_frames[self.current_frame]
            else:
                self.current_frame = 0

        elif self.is_walking:
            if self.current_direction == self.directions[0] and \
                    self.current_frame < self.north_walking_frames.__len__():
                self.texture = self.north_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[1] and \
                    self.current_frame < self.west_walking_frames.__len__():
                self.texture = self.west_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[2] and \
                    self.current_frame < self.south_walking_frames.__len__():
                self.texture = self.south_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[3] and \
                    self.current_frame < self.east_walking_frames.__len__():
                self.texture = self.east_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[4] and \
                    self.current_frame < self.northwest_walking_frames.__len__():
                self.texture = self.northwest_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[5] and \
                    self.current_frame < self.northeast_walking_frames.__len__():
                self.texture = self.northeast_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[6] and \
                    self.current_frame < self.southwest_walking_frames.__len__():
                self.texture = self.southwest_walking_frames[self.current_frame]
            elif self.current_direction == self.directions[7] and \
                    self.current_frame < self.southeast_walking_frames.__len__():
                self.texture = self.southeast_walking_frames[self.current_frame]
            else:
                self.current_frame = 0

        # If the player is idle
        else:
            if self.current_direction == self.directions[0] and \
                    self.current_frame < self.north_idle_frames.__len__():
                self.texture = self.north_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[1] and \
                    self.current_frame < self.west_idle_frames.__len__():
                self.texture = self.west_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[2] and \
                    self.current_frame < self.south_idle_frames.__len__():
                self.texture = self.south_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[3] and \
                    self.current_frame < self.east_idle_frames.__len__():
                self.texture = self.east_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[4] and \
                    self.current_frame < self.northwest_idle_frames.__len__():
                self.texture = self.northwest_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[5] and \
                    self.current_frame < self.northeast_idle_frames.__len__():
                self.texture = self.northeast_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[6] and \
                    self.current_frame < self.southwest_idle_frames.__len__():
                self.texture = self.southwest_idle_frames[self.current_frame]
            elif self.current_direction == self.directions[7] and \
                    self.current_frame < self.southeast_idle_frames.__len__():
                self.texture = self.southeast_idle_frames[self.current_frame]
            else:
                self.current_frame = 0
