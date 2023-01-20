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
        self.player_sprite = None
        self.ghost_sprite = None
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

        # Create the sprites
        self.player_sprite = player.Seraphima(self.map_center_x, self.map_center_y, s.PLAYER_SCALING)
        self.player_list.append(self.player_sprite)
        self.generate_walls(self.level_map.width, self.level_map.height)
        self.ghost_sprite = ghost.GhostMonster(self.map_center_x, self.map_center_y + 200, s.MONSTER_SCALING)
        self.ghost_sprite.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
        self.monster_list.append(self.ghost_sprite)
        self.load_heart_frames()
        for i in range(int(self.health / 10)):
            heart = arcade.Sprite("assets/heart/heart-0.png", s.HEART_SCALING)
            heart.center_x = (self.width - 200) + i * 40
            heart.center_y = 45
            self.heart_list.append(heart)

        # Make the physics engine
        self.player_and_wall_collider = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.player_and_monster_collider = arcade.PhysicsEngineSimple(self.player_sprite, self.monster_list)
        self.monster_and_wall_collider = arcade.PhysicsEngineSimple(self.ghost_sprite, self.wall_list)
        self.camera = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        arcade.set_background_color((108, 121, 147))

        # Make the pathfinding vars
        self.playing_field_left_boundary = 0
        self.playing_field_right_boundary = self.level_map.width * self.level_map.tile_width * s.SPRITE_SCALING
        self.playing_field_top_boundary = self.level_map.height * self.level_map.tile_height * s.SPRITE_SCALING
        self.playing_field_bottom_boundary = 0
        self.grid_size = 128 * s.SPRITE_SCALING
        self.barrier_list = arcade.AStarBarrierList(self.player_sprite, self.wall_list, self.grid_size * 2.5,
                                                    self.playing_field_left_boundary,
                                                    self.playing_field_right_boundary,
                                                    self.playing_field_bottom_boundary,
                                                    self.playing_field_top_boundary)

    def on_draw(self):
        self.camera.use()
        self.channel1.use()
        self.channel1.clear()

        # Draw the path if the debug mode is on
        if arcade.key.T and arcade.key.D in self.key_press_buffer:
            for monster in self.monster_list:
                try:
                    monster.debug_path = arcade.astar_calculate_path(monster.position,
                                                            self.player_sprite.position,
                                                            self.barrier_list,
                                                            diagonal_movement=False)
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
        position = (self.player_sprite.position[0] - self.camera.position[0],
                    self.player_sprite.position[1] - self.camera.position[1])

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
        if arcade.key.T and arcade.key.D in self.key_press_buffer:
            num_ghosts_hunting = 0
            monster_velocities = []
            for monster in self.monster_list:
                if monster.is_hunting:
                    num_ghosts_hunting += 1
                monster_velocities.append((monster.change_x, monster.change_y))
            text = f"Player position: {self.player_sprite.position}.     " \
                   f"Ghosts hunting you: {float(num_ghosts_hunting)}."
            for i in range((len(monster_velocities))):
                ghost_velocity_text = f"\n    Ghost {i} velocity: {monster_velocities[i]}."
                arcade.draw_text(ghost_velocity_text, start_x=40, start_y=838-(i * 26), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
            arcade.draw_text(text, start_x=40, start_y=864, color=(255, 255, 242), font_size=19,
                             font_name="Garamond")

        # Draw game over if dead
        if self.is_dead:
            arcade.draw_text("GAME OVER", start_x=s.SCREEN_WIDTH / 2, start_y=s.SCREEN_HEIGHT / 2,
                             color=(255, 255, 242), font_size=72, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline", bold=True)
            for monster in self.monster_list:
                monster.can_hunt = False

            # If the player isn't already transparent make the player sprite slowly fade out
            if self.player_sprite.alpha != 0:
                self.player_sprite.alpha -= 0.15
                self.player_sprite.alpha = max(0, self.player_sprite.alpha)
            elif not self.is_faded_out:
                self.is_faded_out = True
                self.has_spawned_player_death_ghost = False

            # If the player is fully transparent, spawn a ghost monster on their death location
            elif not self.has_spawned_player_death_ghost:
                self.ghost_sprite = ghost.GhostMonster(self.player_sprite.center_x, self.player_sprite.center_y,
                                                       s.MONSTER_SCALING)
                self.ghost_sprite.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
                self.player_sprite.remove_from_sprite_lists()
                self.monster_list.append(self.ghost_sprite)
                self.has_spawned_player_death_ghost = True

    def on_update(self, delta_time: float = 1 / 120):

        # Update the physics engine
        self.player_and_wall_collider.update()
        self.player_and_monster_collider.update()
        self.monster_and_wall_collider.update()
        self.monster_list.update()
        self.scroll_to_player()
        self.process_key_presses()
        for projectile in self.swordslash_list:
            projectile.update_animation(delta_time)
            projectile.update()
            if arcade.check_for_collision_with_list(projectile, self.wall_list):
                projectile.is_hitting_wall = True

        # Make a projectile if the player is slashing and there currently isn't another one
        if self.player_sprite.is_slashing and self.player_sprite.c_key_timer == 0 and not self.swordslash_list:
            slash_projectile = ss.SwordSlash(self.player_sprite)
            self.swordslash_list.append(slash_projectile)
            arcade.play_sound(random.choice(self.swoosh_sounds), s.SWOOSH_VOLUME)

        # Update the player
        self.player_sprite.update_animation(delta_time)
        if self.player_sprite.c_key_timer > 0:
            self.player_sprite.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

        # Update the heart frames, so they match the animation speed of the player
        self.heart_frame += 9 * delta_time
        for heart in self.heart_list:
            if self.heart_frame < len(self.heart_frames):
                heart.texture = self.heart_frames[int(self.heart_frame)]
            else:
                self.heart_frame = 0

        # Set the first heart's size to represent the player's health
        for heart in self.heart_list:
            heart.scale = (self.health / len(self.heart_list)) / 100
            break

        # Make sure the ghosts cant push the player into a wall
        for monster in self.monster_list:
            if arcade.check_for_collision_with_list(monster, self.wall_list) and \
                    arcade.check_for_collision_with_list(self.player_sprite, self.wall_list):
                monster.change_x *= -1
                monster.change_y *= -1
                monster.bounce_timer = 0.05

        # Handle the player's slash
        player_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.monster_list)
        for projectile in self.swordslash_list:
            projectile_collisions = arcade.check_for_collision_with_list(projectile, self.monster_list)
            for monster in projectile_collisions:
                monster.is_being_hurt = True
        for monster in player_collisions:
            if self.player_sprite.is_slashing:
                monster.is_being_hurt = True
            else:

                # Handle player damage
                self.health -= 1
                if self.health == 0 and self.heart_list:
                    self.heart_list.pop()
                    self.health = s.HEART_HEALTH
                if self.health > 0:
                    continue
                else:
                    self.is_dead = True

        # If a ghost dies increase the counter
        for monster in self.monster_list:
            if monster.health == 0:
                self.score += 1

        # Handle spawning in more monsters if there aren't any on the screen, and it's been a few seconds
        self.spawn_ghosts_on_empty_list()

        # Make sure the new monsters cant walk through walls and bounce off of them if they aren't hunting
        for monster in self.monster_list:
            if arcade.check_for_collision_with_list(monster, self.wall_list) and not monster.is_hunting:
                monster.change_x *= -1
                monster.change_y *= -1

            # Handle the ghosts movement
            elif not monster.is_being_hurt and monster.can_hunt:
                self.move_monster(monster)

        # Play the background music again if it's finished
        if time.time() > self.music_timer:
            arcade.play_sound(arcade.load_sound("sounds/most.mp3"), s.MUSIC_VOLUME)
            self.music_timer = time.time() + (5 * 60) + 57

        # Make sure the player cant get pushed into walls if they are dead
        if self.is_dead:
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0

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
                self.wall_list.append(wall)
            else:
                x = random.randint(100, map_width - 100)
                y = random.randint(100, map_height - 100)
                wall.center_x = x
                wall.center_y = y
            if random.random() < 0.5:
                wall.angle = 90

    def move_monster(self, monster):

        # Try to calculate the path
        if arcade.get_distance_between_sprites(monster, self.player_sprite) < s.MONSTER_VISION_RANGE:
            try:
                self.path = arcade.astar_calculate_path(monster.position,
                                                        self.player_sprite.position,
                                                        self.barrier_list,
                                                        diagonal_movement=False)
                self.path_list.append(self.path)
            except ValueError:
                pass

        if self.path and not self.is_dead and \
                arcade.get_distance_between_sprites(monster, self.player_sprite) < s.MONSTER_VISION_RANGE:

            if not monster.is_hunting:
                monster.is_hunting = True

            # Figure out where we want to go
            try:
                next_x = self.path[monster.current_path_position][0]
                next_y = self.path[monster.current_path_position][1]
            except IndexError:
                # We are at the end of the path
                next_x = self.player_sprite.center_x
                next_y = self.player_sprite.center_y

            # What's the difference between the two
            diff_x = next_x - monster.center_x
            diff_y = next_y - monster.center_y

            # What's our angle
            angle = math.atan2(diff_y, diff_x)

            # Calculate the travel vector
            monster.change_x = math.cos(angle) * s.MONSTER_MOVEMENT_SPEED
            monster.change_y = math.sin(angle) * s.MONSTER_MOVEMENT_SPEED

            # Check if the speed is less than 0.7 units
            speed = math.sqrt(monster.change_x ** 2 + monster.change_y ** 2)
            if speed < 0.7:
                monster.change_x = monster.change_x * 0.7 / speed
                monster.change_y = monster.change_y * 0.7 / speed

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
                monster.change_x = random.randint(-s.MONSTER_MOVEMENT_SPEED, s.MONSTER_MOVEMENT_SPEED)
                monster.change_y = random.randint(-s.MONSTER_MOVEMENT_SPEED, s.MONSTER_MOVEMENT_SPEED)

    def spawn_ghosts(self):
        for i in range(int(self.ghosts_to_spawn)):
            random_x = random.uniform(self.player_sprite.center_x - 50, self.player_sprite.center_x + 50)
            random_y = random.uniform(self.player_sprite.center_y - 50, self.player_sprite.center_y + 50)
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
            if monster.collides_with_sprite(self.player_sprite):
                collision = True
            if not collision:
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
        position = Vec2(self.player_sprite.center_x - self.width / 2,
                        self.player_sprite.center_y - self.height / 2)
        self.camera.move_to(position, speed)

    def on_key_press(self, key, modifiers):
        if not self.is_dead:
            self.key_press_buffer.add(key)

    def process_key_presses(self):
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        # Handle slashing, hold the c key for SLASH_CHARGE_TIME to activate
        # This discourages spamming the slash key
        if arcade.key.C in self.key_press_buffer:
            if self.player_sprite.c_key_timer == 0:
                self.player_sprite.c_key_timer = time.time()
            elif time.time() - self.player_sprite.c_key_timer >= s.SLASH_CHARGE_TIME:
                self.player_sprite.is_slashing = True
                self.player_sprite.c_key_timer = 0

        # Handle running, hold the shift key
        if arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "northwest"
            self.player_sprite.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "southwest"
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "northeast"
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer \
                and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7 * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "southeast"
            self.player_sprite.is_running = True
        elif arcade.key.UP in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "north"
            self.player_sprite.is_running = True
        elif arcade.key.DOWN in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            self.player_sprite.current_direction = "south"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.is_running = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            self.player_sprite.current_direction = "west"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.is_running = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.LSHIFT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * s.PLAYER_RUN_SPEED_MODIFIER
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER
            self.player_sprite.current_direction = "east"
            self.player_sprite.is_running = True

        # Handle basic movement use the arrow keys
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "northwest"
            self.player_sprite.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "southwest"
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "northeast"
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer and arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED * 0.7
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED * 0.7
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.current_direction = "southeast"
            self.player_sprite.is_walking = True
        elif arcade.key.UP in self.key_press_buffer:
            self.player_sprite.change_y = s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "north"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.DOWN in self.key_press_buffer:
            self.player_sprite.change_y = -s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "south"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_y *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.LEFT in self.key_press_buffer:
            self.player_sprite.change_x = -s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "west"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True
        elif arcade.key.RIGHT in self.key_press_buffer:
            self.player_sprite.change_x = s.PLAYER_MOVEMENT_SPEED
            self.player_sprite.current_direction = "east"
            if self.player_sprite.is_slashing:
                self.player_sprite.change_x *= s.SLASH_SPEED_MODIFIER + (s.SLASH_SPEED_MODIFIER / 3)
            self.player_sprite.is_walking = True

        # Modify the movement speed again to make a charge effect when c is pressed
        if arcade.key.C in self.key_press_buffer:
            self.player_sprite.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.player_sprite.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

    def on_key_release(self, key, modifiers):
        self.key_press_buffer.discard(key)
        if not self.key_press_buffer:
            if self.player_sprite.is_walking:
                self.player_sprite.is_walking = False
            if self.player_sprite.is_running:
                self.player_sprite.is_running = False
                self.player_sprite.just_stopped_running = True
        elif arcade.key.C not in self.key_press_buffer:
            self.player_sprite.c_key_timer = 0


if __name__ == "__main__":
    window = MyGame(s.SCREEN_WIDTH, s.SCREEN_HEIGHT, s.SCREEN_TITLE)
    window.set_location(1025, 35)
    arcade.run()
