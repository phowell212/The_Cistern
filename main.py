import math
import random
import arcade
import time
import ghost
import player
import settings as s
import swordslash as ss
from arcade.experimental import Shadertoy
from pathlib import Path
from pyglet.math import Vec2


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)

        # Init the shaders
        self.box_shadertoy = None
        self.channel0 = None
        self.channel1 = None
        self.load_shader()

        # Init the sprites
        self.seraphima = None
        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.swordslash_list = arcade.SpriteList()
        self.heart_list = arcade.SpriteList()
        self.heart_frames = []
        self.heart_frame = 0

        # Init counters, constants, arrays, flags, and sounds
        self.key_press_buffer = set()
        self.ghosts_to_spawn = 2.0
        self.ghosts_to_spawn_multiplier = 1.25
        self.no_ghost_timer = 0.0
        self.score = 0
        self.music_timer = time.time()
        self.general_timer = time.time()
        self.health = s.PLAYER_STARTING_HEALTH
        self.is_dead = False
        self.is_faded_out = False
        self.has_spawned_player_death_ghost = True
        self.swoosh_sounds = []
        for i in range(0, 3):
            self.swoosh_sounds.append(arcade.load_sound(f"sounds/sword_swoosh-{i}.mp3"))
        arcade.play_sound(arcade.load_sound("sounds/most.mp3"), s.MUSIC_VOLUME)
        self.music_timer = time.time() + (5 * 60) + 57

        # Init the pathfinding vars
        self.path = None
        self.barrier_list = None
        self.path_list = []

        # Load the level map
        map_location = "assets/level/level_map.json"
        layer_options = {"Tile Layer 1": {"use_spatial_hash": True, "spatial_hash_cell_size": 128}}
        self.level_map = arcade.tilemap.load_tilemap(map_location, s.SPRITE_SCALING, layer_options=layer_options)
        self.map_center_x = self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING / 2
        self.map_center_y = self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING / 2
        self.wall_tile_map = arcade.load_tilemap(map_location, s.SPRITE_SCALING, layer_options)
        self.wall_tile_map = arcade.Scene.from_tilemap(self.wall_tile_map)
        scene_wall_sprite_list = self.wall_tile_map.get_sprite_list("Tile Layer 1")
        self.wall_list.extend(scene_wall_sprite_list)
        self.generate_walls(self.level_map.width, self.level_map.height)

        # Create playing field sprites
        self.seraphima = player.Player(self.map_center_x, self.map_center_y, s.PLAYER_SCALING)
        self.player_list.append(self.seraphima)
        self.spawn_ghosts_on_empty_list()
        self.load_heart_frames()
        for i in range(int(self.health / 10)):
            heart = arcade.Sprite("assets/heart/heart-0.png", s.HEART_SCALING)
            heart.center_x = (self.width - 200) + i * 40
            heart.center_y = 45
            self.heart_list.append(heart)
        self.heart_list.reverse()

        # Make the physics engine
        self.player_and_wall_collider = arcade.PhysicsEngineSimple(self.seraphima, self.wall_list)
        self.player_and_monster_collider = arcade.PhysicsEngineSimple(self.seraphima, self.monster_list)
        self.camera = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        self.monster_phys_engines = []
        arcade.set_background_color((108, 121, 147))

        # Make the pathfinding vars
        self.playing_field_left_boundary = 0
        self.playing_field_right_boundary = self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING
        self.playing_field_top_boundary = self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING
        self.playing_field_bottom_boundary = 0
        self.grid_size = 128 * s.SPRITE_SCALING
        self.barrier_list = arcade.AStarBarrierList(self.seraphima, self.wall_list, self.grid_size,
                                                    self.playing_field_left_boundary,
                                                    self.playing_field_right_boundary,
                                                    self.playing_field_bottom_boundary,
                                                    self.playing_field_top_boundary)

    def on_draw(self):
        self.camera.use()
        self.channel1.use()
        self.channel1.clear()

        # Draw the path if the debug mode is on
        if arcade.key.D in self.key_press_buffer:
            for monster in self.monster_list:
                try:
                    monster.debug_path = arcade.astar_calculate_path(monster.position,
                                                                     self.seraphima.position,
                                                                     self.barrier_list,
                                                                     diagonal_movement=True)
                except ValueError:
                    pass
                if monster.debug_path is not None:
                    arcade.draw_line_strip(monster.debug_path, (30, 33, 40), 2)
        self.path_list = []
        self.monster_list.draw()

        # Draw the walls
        self.channel0.use()
        self.channel0.clear()
        self.wall_list.draw()
        self.use()
        self.clear()

        # Calculate the light position
        position = (self.seraphima.position[0] - self.camera.position[0],
                    self.seraphima.position[1] - self.camera.position[1])

        # Run the shader and render to the window
        self.box_shadertoy.program['lightPosition'] = position
        self.box_shadertoy.program['lightSize'] = s.SPOTLIGHT_SIZE
        self.box_shadertoy.render()

        # Draw the player
        self.player_list.draw()
        self.swordslash_list.draw()

        # Draw the GUI
        self.camera_gui.use()
        self.heart_list.draw()

        # Draw our score on the screen, scrolling it with the viewport
        # the score is increased 11 times per monster killed, so we divide it by 11 to get the actual score
        score_text = f"Score: {self.score / 11}     Ghosts: {float(len(self.monster_list))}"
        arcade.draw_text(score_text, start_x=40, start_y=32, color=(255, 255, 242), font_size=19,
                         font_name="Garamond")

        # Draw the debug info if the debug mode is on
        if arcade.key.D in self.key_press_buffer:
            num_ghosts_hunting = 0
            monster_velocities = []
            for monster in self.monster_list:
                if monster.is_hunting:
                    num_ghosts_hunting += 1
                monster_velocities.append((monster.change_x, monster.change_y))
            text = f"Player position: {self.seraphima.position}.     " \
                   f"Ghosts hunting you: {float(num_ghosts_hunting)}."
            for i in range((len(monster_velocities))):
                ghost_velocity_text = f"\n    Ghost {i} velocity: {monster_velocities[i]}.   "
                arcade.draw_text(ghost_velocity_text, start_x=40, start_y=834 - (i * 30 * 2), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
                ghost_position_text = f"Ghost {i} position: {self.monster_list[i].position}."
                arcade.draw_text(ghost_position_text, start_x=90, start_y=804 - (i * 30 * 2), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
            arcade.draw_text(text, start_x=40, start_y=864, color=(255, 255, 242), font_size=19,
                             font_name="Garamond")

        # Draw game over if dead
        if not self.heart_list:
            arcade.draw_text("GAME OVER", start_x=s.SCREEN_WIDTH / 2, start_y=s.SCREEN_HEIGHT / 2,
                             color=(255, 255, 242), font_size=72, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline", bold=True)
            for monster in self.monster_list:
                monster.can_hunt = False

            # If the player isn't already transparent make the player sprite slowly fade out
            if self.seraphima.alpha != 0:
                self.seraphima.alpha -= 0.15
                self.seraphima.alpha = max(0, self.seraphima.alpha)
            elif not self.is_faded_out:
                self.is_faded_out = True
                self.has_spawned_player_death_ghost = False

            # If the player is fully transparent, spawn a ghost monster on their death location
            elif not self.has_spawned_player_death_ghost:
                self.ghost_sprite = ghost.GhostMonster(self.seraphima.center_x, self.seraphima.center_y,
                                                       s.MONSTER_SCALING)
                self.ghost_sprite.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
                self.seraphima.remove_from_sprite_lists()
                self.monster_list.append(self.ghost_sprite)
                self.has_spawned_player_death_ghost = True

    def on_update(self, delta_time: float = 1 / 120):

        # Update the physics engine
        if not self.is_dead:
            self.player_and_monster_collider = arcade.PhysicsEngineSimple(self.seraphima, self.monster_list)
            self.player_and_monster_collider.update()
            self.player_and_wall_collider.update()

        # Update the movement of the monsters, projectiles, and camera
        self.monster_list.update()
        self.scroll_to_player()
        self.process_key_presses()
        for projectile in self.swordslash_list:
            projectile.update_animation(delta_time)
            projectile.update()
            if arcade.check_for_collision_with_list(projectile, self.wall_list):
                projectile.is_hitting_wall = True

        # Make a projectile if the player is slashing and there currently isn't another one
        if self.seraphima.is_slashing and self.seraphima.c_key_timer == 0 and not self.swordslash_list:
            slash_projectile = ss.SwordSlash(self.seraphima)
            self.swordslash_list.append(slash_projectile)
            arcade.play_sound(random.choice(self.swoosh_sounds), s.SWOOSH_VOLUME)

        # Update the player
        self.seraphima.update_animation(delta_time)
        if self.seraphima.c_key_timer > 0:
            self.seraphima.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.seraphima.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

        # Update the heart frames, so they match the animation speed of the player
        self.heart_frame += 18 * delta_time
        for heart in self.heart_list:
            if self.heart_frame < len(self.heart_frames):
                heart.texture = self.heart_frames[int(self.heart_frame)]
            else:
                self.heart_frame = 0

        # Set the first heart's size to represent the player's health
        for heart in self.heart_list:
            heart.scale = (self.health / len(self.heart_list)) / 100
            break

        # Handle the player's slash
        player_collisions = arcade.check_for_collision_with_list(self.seraphima, self.monster_list)
        for projectile in self.swordslash_list:
            projectile_collisions = arcade.check_for_collision_with_list(projectile, self.monster_list)
            for monster in projectile_collisions:
                monster.is_being_hurt = True
        for monster in player_collisions:
            if self.seraphima.is_slashing:
                monster.is_being_hurt = True
                self.handle_player_damage()
            else:
                self.handle_player_damage()

        # If a ghost dies increase the counter
        for monster in self.monster_list:
            if monster.health == 0:
                self.score += 1

        # Handle spawning in more monsters if there aren't any on the screen, and it's been a few seconds
        self.spawn_ghosts_on_empty_list()

        for monster in self.monster_list:
            if not monster.is_being_hurt:
                self.move_monster(monster)

            # Make the monster respawn_monster if they move off the play area
            if monster.center_x < 0 or \
                    monster.center_x > self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING:
                self.respawn_monster(monster)
            if monster.center_y < 0 or \
                    monster.center_y > self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING:
                self.respawn_monster(monster)

        # Update our own hacky monster physics engine cause you cant access the monster inside a simple physics engine
        self.update_monster_physics()

        # Play the background music again if it's finished
        if time.time() > self.music_timer:
            arcade.play_sound(arcade.load_sound("sounds/most.mp3"), s.MUSIC_VOLUME)
            self.music_timer = time.time() + (5 * 60) + 57

    def load_shader(self):
        shader_file_path = Path("shaders/level_1_shader.glsl")
        window_size = self.get_size()
        self.box_shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.box_shadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadertoy.ctx.texture(window_size, components=4)])
        self.channel1 = self.box_shadertoy.ctx.framebuffer(
            color_attachments=[self.box_shadertoy.ctx.texture(window_size, components=4)])

        # Assign the frame buffers to the channels
        self.box_shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.box_shadertoy.channel_1 = self.channel1.color_attachments[0]

    def load_heart_frames(self):
        for i in range(0, 7):
            self.heart_frames.append(arcade.load_texture(f"assets/heart/heart-{i}.png"))

    def generate_walls(self, map_width, map_height):
        map_width = int(map_width * self.level_map.tile_width * s.SPRITE_SCALING)
        map_height = int(map_height * self.level_map.tile_height * s.SPRITE_SCALING)
        for _ in range(150):
            x = random.randint(100, map_width - 100)
            y = random.randint(100, map_height - 100)
            wall = arcade.Sprite("assets/level/wall.png", s.SPRITE_SCALING)
            wall.center_x = x
            wall.center_y = y
            overlap = False
            for wall_check in self.wall_list:
                if wall.collides_with_sprite(wall_check):
                    overlap = True
                    break
                elif wall.collides_with_list(self.player_list):
                    overlap = True
                    break
            if not overlap:
                if random.random() > 0.5:
                    wall.angle = 45
                if random.random() > 0.9:
                    wall.scale *= random.randint(50, 200) / 100
                if random.random() > 0.9:
                    wall.scale *= random.randint(50, 200) / 100
                self.wall_list.append(wall)
            else:
                x = random.randint(100, map_width - 100)
                y = random.randint(100, map_height - 100)
                wall.center_x = x
                wall.center_y = y

    def handle_player_damage(self):
        self.health -= 1
        if self.health == 0 and self.heart_list:
            self.heart_list.pop()
            self.health = s.HEART_HEALTH
        if self.health < 0:
            self.is_dead = True

    def move_monster(self, monster):

        # Try to calculate the path
        if arcade.get_distance_between_sprites(monster, self.seraphima) < s.MONSTER_VISION_RANGE:
            self.path = arcade.astar_calculate_path(monster.position,
                                                    self.seraphima.position,
                                                    self.barrier_list,
                                                    diagonal_movement=False)
            self.path_list.append(self.path)
        if self.path and not self.is_dead and \
                arcade.get_distance_between_sprites(monster, self.seraphima) < s.MONSTER_VISION_RANGE:
            if not monster.is_hunting:
                monster.is_hunting = True

            # Figure out where we want to go
            try:
                next_x = self.path[monster.current_path_position][0]
                next_y = self.path[monster.current_path_position][1]
            except IndexError:

                # We are at the end of the path
                next_x = self.seraphima.center_x
                next_y = self.seraphima.center_y

            # What's the difference between the two
            diff_x = next_x - monster.center_x
            diff_y = next_y - monster.center_y

            # What's our angle
            angle = math.atan2(diff_y, diff_x)

            # Calculate the travel vector
            monster.change_x = math.cos(angle) * s.MONSTER_MOVEMENT_SPEED
            monster.change_y = math.sin(angle) * s.MONSTER_MOVEMENT_SPEED
            if (monster.change_y ** 2 + monster.change_x ** 2) ** 0.5 > s.MONSTER_MOVEMENT_SPEED:
                monster.change_x += s.MONSTER_MOVEMENT_SPEED * monster.change_x / abs(monster.change_x)
                monster.change_y += s.MONSTER_MOVEMENT_SPEED * monster.change_y / abs(monster.change_y)

            # Recalculate distance after the move
            distance = math.sqrt((monster.center_x - next_x) ** 2 + (monster.center_y - next_y) ** 2)

            # If we're close enough, move to the next point
            if distance < s.MONSTER_MOVEMENT_SPEED:
                monster.current_path_position += 1

                # If we're at the end of the path, start over
                if monster.current_path_position >= len(self.path):
                    monster.current_path_position = 0
        else:
            if monster.is_hunting:
                monster.is_hunting = False

            # If we can't find a path, or are far enough away from the player just move randomly:
            if random.randint(0, 100) == 0:
                monster.change_x = random.randint(int(-s.MONSTER_MOVEMENT_SPEED), int(s.MONSTER_MOVEMENT_SPEED))
                monster.change_y = random.randint(int(-s.MONSTER_MOVEMENT_SPEED), int(s.MONSTER_MOVEMENT_SPEED))

    def respawn_monster(self, monster):
        spawn_x = random.randint(0, self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING)
        spawn_y = random.randint(0, self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING)
        distance = math.sqrt(
            (spawn_x - self.seraphima.center_x) ** 2 + (spawn_y - self.seraphima.center_y) ** 2)
        while distance < s.SPOTLIGHT_SIZE:
            spawn_x = random.randint(0, self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING)
            spawn_y = random.randint(0,
                                     self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING)
            distance = math.sqrt(
                (spawn_x - self.seraphima.center_x) ** 2 + (spawn_y - self.seraphima.center_y) ** 2)
        monster.center_x = spawn_x
        monster.center_y = spawn_y

    def spawn_ghosts(self):
        for i in range(int(self.ghosts_to_spawn)):
            random_x = random.uniform(self.seraphima.center_x - 50, self.seraphima.center_x + 50)
            random_y = random.uniform(self.seraphima.center_y - 50, self.seraphima.center_y + 50)
            if random_x < 0 or random_x > self.level_map.width or random_y < 0 or \
                    random_y > self.level_map.height:
                random_x = random.uniform(0, self.width)
                random_y = random.uniform(0, self.height)
            monster = ghost.GhostMonster(random_x, random_y, s.MONSTER_SCALING)
            monster.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")

            # Check if the new monster collides with any existing monsters, wall sprites or player
            collision = False
            for wall in self.wall_list:
                if monster.collides_with_sprite(wall):
                    collision = True
                    break
            if monster.collides_with_sprite(self.seraphima):
                collision = True
            if not collision:
                if random.random() > 0.9:
                    monster.scale *= random.randint(50, 250) / 100
                if random.random() > 0.95:
                    monster.scale *= random.randint(60, 150) / 100
                self.monster_list.append(monster)
            else:

                # If there is a collision, Don't spawn the monster and try again
                self.ghosts_to_spawn += 1

    def spawn_ghosts_on_empty_list(self):

        # Handle spawning in more monsters if there aren't any on the screen, and it's been a few seconds
        if not self.monster_list:
            if self.no_ghost_timer != 0:
                self.no_ghost_timer = time.time()
            elif time.time() - self.no_ghost_timer > 5:
                self.spawn_ghosts()

                # Reset the timer and increase the number of ghosts to spawn
                self.ghosts_to_spawn += 0.5
            self.ghosts_to_spawn *= self.ghosts_to_spawn_multiplier
            self.no_ghost_timer = 0.0

    def scroll_to_player(self, speed=s.CAMERA_SPEED):
        position = Vec2(self.seraphima.center_x - self.width / 2,
                        self.seraphima.center_y - self.height / 2)
        self.camera.move_to(position, speed)

    def update_monster_physics(self):
        for monster in self.monster_list:
            for wall in self.wall_list:
                if arcade.check_for_collision(monster, wall):
                    if not monster.is_hunting:
                        monster.change_x = -monster.change_x
                        monster.change_y = -monster.change_y
                        if monster.change_x > 0 and monster.right >= wall.left:
                            monster.center_x += 1
                        elif monster.change_x < 0 and monster.left <= wall.right:
                            monster.center_x -= 1
                        elif monster.change_y > 0 and monster.top >= wall.bottom:
                            monster.center_y += 1
                        elif monster.change_y < 0 and monster.bottom <= wall.top:
                            monster.center_y -= 1
                    else:
                        if monster.change_x > 0 and monster.right >= wall.left:
                            monster.change_x = 0
                            monster.center_x += 1
                        elif monster.change_x < 0 and monster.left <= wall.right:
                            monster.change_x = 0
                            monster.center_x -= 1
                        elif monster.change_y > 0 and monster.top >= wall.bottom:
                            monster.change_y = 0
                            monster.center_y += 1
                        elif monster.change_y < 0 and monster.bottom <= wall.top:
                            monster.change_y = 0
                            monster.center_y -= 1

    def on_key_press(self, key, modifiers):
        if self.heart_list:
            self.key_press_buffer.add(key)

    def process_key_presses(self):
        self.seraphima.change_x = 0
        self.seraphima.change_y = 0

        # Handle slashing, hold the c key for SLASH_CHARGE_TIME to activate
        # This discourages spamming the slash key
        if arcade.key.C in self.key_press_buffer:
            if self.seraphima.c_key_timer == 0:
                self.seraphima.c_key_timer = time.time()
            elif time.time() - self.seraphima.c_key_timer >= s.SLASH_CHARGE_TIME:
                self.seraphima.is_slashing = True
                self.seraphima.c_key_timer = 0

        # Handle running, use the arrow keys
        if arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.seraphima.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER
            self.seraphima.current_direction = "northwest"
            self.seraphima.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.seraphima.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER
            self.seraphima.current_direction = "southwest"
            self.seraphima.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.seraphima.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER
            self.seraphima.current_direction = "northeast"
            self.seraphima.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.seraphima.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER
            self.seraphima.current_direction = "southeast"
            self.seraphima.is_running = True
        elif arcade.key.UP in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_y = s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            if self.seraphima.is_slashing:
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER
            self.seraphima.current_direction = "north"
            self.seraphima.is_running = True
        elif arcade.key.DOWN in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_y = -s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            self.seraphima.current_direction = "south"
            if self.seraphima.is_slashing:
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER
            self.seraphima.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_x = -s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            self.seraphima.current_direction = "west"
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER
            self.seraphima.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and not arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.change_x = s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER
            self.seraphima.current_direction = "east"
            self.seraphima.is_running = True

        # Handle walking, hold the shift key
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.seraphima.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.seraphima.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.current_direction = "northwest"
            self.seraphima.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.seraphima.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.seraphima.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.current_direction = "southwest"
            self.seraphima.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.seraphima.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.seraphima.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.current_direction = "northeast"
            self.seraphima.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.seraphima.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.seraphima.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.current_direction = "southeast"
            self.seraphima.is_walking = True
        elif arcade.key.UP in self.key_press_buffer:
            self.seraphima.change_y = s.PLAYER_MOVEMENT_SPEED
            self.seraphima.current_direction = "north"
            if self.seraphima.is_slashing:
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.is_walking = True
        elif arcade.key.DOWN in self.key_press_buffer:
            self.seraphima.change_y = -s.PLAYER_MOVEMENT_SPEED
            self.seraphima.current_direction = "south"
            if self.seraphima.is_slashing:
                self.seraphima.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer:
            self.seraphima.change_x = -s.PLAYER_MOVEMENT_SPEED
            self.seraphima.current_direction = "west"
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer:
            self.seraphima.change_x = s.PLAYER_MOVEMENT_SPEED
            self.seraphima.current_direction = "east"
            if self.seraphima.is_slashing:
                self.seraphima.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.seraphima.is_walking = True

        # Modify the movement speed again to make a charge effect when c is pressed
        if arcade.key.C in self.key_press_buffer:
            self.seraphima.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.seraphima.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

        # Make sure the player is not running if the shift key is pressed
        if arcade.key.LSHIFT in self.key_press_buffer:
            self.seraphima.is_running = False

    def on_key_release(self, key, modifiers):
        self.key_press_buffer.discard(key)
        if not self.key_press_buffer:
            if self.seraphima.is_walking:
                self.seraphima.is_walking = False
            if self.seraphima.is_running:
                self.seraphima.is_running = False
                self.seraphima.just_stopped_running = True
        elif arcade.key.C not in self.key_press_buffer:
            self.seraphima.c_key_timer = 0


if __name__ == "__main__":
    window = MyGame(s.SCREEN_WIDTH, s.SCREEN_HEIGHT, s.SCREEN_TITLE)
    window.set_location(0, 30)
    arcade.run()
