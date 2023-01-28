import math
import random
import arcade
import time
import player
import swordslash
import darkfairy
import darkfairy_spell
import settings as s
import ghost as g
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
        self.ghost_list = arcade.SpriteList()
        self.swordslash_list = arcade.SpriteList()
        self.heart_list = arcade.SpriteList()
        self.boss_list = arcade.SpriteList()
        self.dark_fairy_spell_list = arcade.SpriteList()
        self.heart_frames = []
        self.heart_frame = 0

        # Init counters, constants, arrays, flags, and sounds
        self.key_press_buffer = set()
        self.ghosts_to_spawn = 4.0
        self.ghosts_to_spawn_multiplier = 1.4
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
        self.player_and_ghost_collider = None
        self.player_and_boss_collider = None
        self.boss_and_wall_collider = None
        self.ghost_and_wall_collider = None
        self.ghost_and_ghost_collider = None
        self.ghost_and_boss_collider = None
        self.camera = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
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

        self.draw_debug_paths()
        self.draw_ghosts()
        self.draw_walls()
        self.draw_player()
        self.draw_gui()
        self.draw_debug_info()
        self.draw_game_over()

    def on_update(self, delta_time: float = 1 / 60):
        self.update_physics()
        self.update_movement(delta_time)
        self.update_projectiles()
        self.update_seraphima(delta_time)
        self.update_gui(delta_time)
        self.update_ghosts()
        self.update_bosses()
        self.update_music()

    def on_key_press(self, key, modifiers):
        if self.heart_list:
            self.key_press_buffer.add(key)

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

    def draw_debug_paths(self):
        if arcade.key.D in self.key_press_buffer:
            for ghost in self.ghost_list:
                try:
                    ghost.debug_path = arcade.astar_calculate_path(ghost.position,
                                                                   self.seraphima.position,
                                                                   self.barrier_list,
                                                                   diagonal_movement=True)
                except ValueError:
                    pass
                if ghost.debug_path is not None:
                    arcade.draw_line_strip(ghost.debug_path, (30, 33, 40), 2)

            for boss in self.boss_list:
                try:
                    boss.debug_path = arcade.astar_calculate_path(boss.position,
                                                                  self.seraphima.position,
                                                                  self.barrier_list,
                                                                  diagonal_movement=True)
                except ValueError:
                    pass
                if boss.debug_path is not None:
                    arcade.draw_line_strip(boss.debug_path, (30, 33, 40), 2)

            for spell in self.dark_fairy_spell_list:
                try:
                    spell.debug_path = arcade.astar_calculate_path(spell.position,
                                                                   self.seraphima.position,
                                                                   self.barrier_list,
                                                                   diagonal_movement=True)
                except ValueError:
                    pass
                if spell.debug_path is not None:
                    arcade.draw_line_strip(spell.debug_path, (30, 33, 40), 2)

    def draw_ghosts(self):
        self.ghost_list.draw()
        self.boss_list.draw()
        self.dark_fairy_spell_list.draw()

    def draw_walls(self):
        self.channel0.use()
        self.channel0.clear()
        self.wall_list.draw()
        self.use()
        self.clear()

    def draw_player(self):
        position = (self.seraphima.position[0] - self.camera.position[0],
                    self.seraphima.position[1] - self.camera.position[1])

        self.box_shadertoy.program['lightPosition'] = position
        self.box_shadertoy.program['lightSize'] = s.SPOTLIGHT_SIZE
        self.box_shadertoy.render()

        self.player_list.draw()
        self.swordslash_list.draw()

    def draw_gui(self):
        self.camera_gui.use()
        self.heart_list.draw()
        score_text = f"Score: {int(self.score / 6.5)}.0"
        for ghost in self.ghost_list:
            if ghost.death_frame > 0:
                score_text = f"Score: {self.score / 6.5}"
                break
        ghost_text = f"Ghosts: {len(self.ghost_list)}.0"
        arcade.draw_text(ghost_text, start_x=40, start_y=70, color=(255, 255, 242), font_size=19,
                         font_name="Garamond")
        arcade.draw_text(score_text, start_x=40, start_y=32, color=(255, 255, 242), font_size=19,
                         font_name="Garamond")

    def draw_debug_info(self):
        if arcade.key.D in self.key_press_buffer:
            num_ghosts_hunting = 0
            ghost_velocities = []
            for ghost in self.ghost_list:
                if ghost.is_hunting:
                    num_ghosts_hunting += 1
                ghost_velocities.append((ghost.change_x, ghost.change_y))
            text = f"Player position: ({int(self.seraphima.position[0])}, {int(self.seraphima.position[1])}), " \
                   f" ({int(self.seraphima.top)}, {int(self.seraphima.left)}, " \
                   f"{int(self.seraphima.bottom)}, {int(self.seraphima.right)})."
            ghost_hunting_text = f"Ghosts hunting you: {num_ghosts_hunting}."
            arcade.draw_text(ghost_hunting_text, start_x=40, start_y=964, color=(255, 255, 242), font_size=19,
                             font_name="Garamond")
            for i in range((len(ghost_velocities))):
                ghost_velocity_text = f"\n    Ghost {i} velocity: ({ghost_velocities[i][0]}, " \
                                      f" {ghost_velocities[i][1]})."
                ghost_position_text = f"Ghost {i} position: ({int(self.ghost_list[i].position[0])}, " \
                                      f" {int(self.ghost_list[i].position[1])})."
                arcade.draw_text(ghost_velocity_text, start_x=40, start_y=904 - (i * 30 * 2), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
                arcade.draw_text(ghost_position_text, start_x=90, start_y=874 - (i * 30 * 2), color=(255, 255, 242),
                                 font_size=19, font_name="Garamond")
                if i == 4:
                    break
            arcade.draw_text(text, start_x=40, start_y=934, color=(255, 255, 242), font_size=19,
                             font_name="Garamond")

    def draw_game_over(self):
        if not self.heart_list:
            arcade.draw_text("GAME OVER", start_x=s.SCREEN_WIDTH / 2, start_y=s.SCREEN_HEIGHT / 2,
                             color=(255, 255, 242), font_size=72, font_name="Garamond", anchor_x="center",
                             anchor_y="baseline", bold=True)
            for ghost in self.ghost_list:
                ghost.can_hunt = False

            # If the player isn't already transparent make the player sprite slowly fade out
            if self.seraphima.alpha != 0:
                self.seraphima.alpha -= 0.03 * self.seraphima.alpha
                self.seraphima.alpha = max(0, self.seraphima.alpha)
            elif not self.is_faded_out:
                self.is_faded_out = True
                self.has_spawned_player_death_ghost = False

            # If the player is fully transparent, spawn a ghost on their death location
            elif not self.has_spawned_player_death_ghost:
                ghost_sprite = g.GhostMonster(self.seraphima.center_x, self.seraphima.center_y,
                                              s.PLAYER_SCALING)
                ghost_sprite.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")
                self.seraphima.remove_from_sprite_lists()
                self.ghost_list.append(ghost_sprite)
                self.has_spawned_player_death_ghost = True

    def update_physics(self):
        if self.heart_list:
            self.player_and_ghost_collider = arcade.PhysicsEngineSimple(self.seraphima, self.ghost_list)
            self.player_and_ghost_collider.update()
            self.player_and_wall_collider.update()

        if self.boss_list:
            for boss in self.boss_list:
                self.boss_and_wall_collider = arcade.PhysicsEngineSimple(boss, self.wall_list)
                self.boss_and_wall_collider.update()
                self.player_and_boss_collider = arcade.PhysicsEngineSimple(self.seraphima, self.boss_list)
                self.player_and_boss_collider.update()

        for ghost in self.ghost_list:
            self.ghost_and_wall_collider = arcade.PhysicsEngineSimple(ghost, self.wall_list)
            self.ghost_and_wall_collider.update()
            self.ghost_and_ghost_collider = arcade.PhysicsEngineSimple(ghost, self.ghost_list)
            self.ghost_and_ghost_collider.update()
            if self.boss_list:
                self.ghost_and_boss_collider = arcade.PhysicsEngineSimple(ghost, self.boss_list)
                self.ghost_and_boss_collider.update()

    def update_movement(self, delta_time):
        self.ghost_list.update()
        self.scroll_to_player()
        self.process_key_presses()
        for projectile in self.swordslash_list:
            projectile.update_animation(delta_time)
            projectile.update()
            if arcade.check_for_collision_with_list(projectile, self.wall_list):
                projectile.is_hitting_wall = True

        # Decrease the player's speed when a boss is out because for whatever reason the player's speed is increased
        # when more bosses are spawned
        if self.boss_list:
            for _ in self.boss_list:
                self.seraphima.change_x *= 0.8
                self.seraphima.change_y *= 0.8

    def update_projectiles(self):
        if self.seraphima.is_slashing and self.seraphima.c_key_timer == 0 and not self.swordslash_list:
            slash_projectile = swordslash.SwordSlash(self.seraphima)
            self.swordslash_list.append(slash_projectile)
            arcade.play_sound(random.choice(self.swoosh_sounds), s.SWOOSH_VOLUME)

        for projectile in self.swordslash_list:
            projectile_collisions = arcade.check_for_collision_with_list(projectile, self.ghost_list)
            for ghost in projectile_collisions:
                ghost.is_being_hurt = True
            boss_collisions = arcade.check_for_collision_with_list(projectile, self.boss_list)
            for boss in boss_collisions:
                self.handle_boss_damage(boss)

        for spell in self.dark_fairy_spell_list:
            spell.update()
            self.move_spell(spell)
            spell_collisions = arcade.check_for_collision_with_list(spell, self.ghost_list)
            for ghost in spell_collisions:
                ghost.is_being_hurt = True
            if arcade.check_for_collision(spell, self.seraphima):
                self.handle_player_damage()

        player_collisions = arcade.check_for_collision_with_list(self.seraphima, self.ghost_list)
        for ghost in player_collisions:
            if self.seraphima.is_slashing:
                ghost.is_being_hurt = True
            self.handle_player_damage()

    def update_seraphima(self, delta_time):
        self.seraphima.update_animation(delta_time)
        if self.seraphima.c_key_timer > 0:
            self.seraphima.change_x *= s.SLASH_CHARGE_SPEED_MODIFIER
            self.seraphima.change_y *= s.SLASH_CHARGE_SPEED_MODIFIER

    def update_gui(self, delta_time):
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

        # If a ghost dies increase the counter
        for ghost in self.ghost_list:
            if ghost.health == 0:
                self.score += 1 * ghost.scale

        # If the boss dies increase the counter
        for boss in self.boss_list:
            if boss.health == 0 and boss.phase == 2:
                self.score += 11

    def update_ghosts(self):
        self.spawn_ghosts_on_empty_list()
        for ghost in self.ghost_list:
            if not ghost.is_being_hurt:
                self.move_ghost(ghost)
            if ghost.left < 0 or ghost.top > 2559 or ghost.right > 2559 or ghost.bottom < 0:
                ghost.health = 0

    def update_bosses(self):
        if self.boss_list:
            self.move_boss()

            # Let the boss cast spells
            for boss in self.boss_list:
                if (random.randint(0, 90) == 0 and arcade.get_distance_between_sprites(self.seraphima, boss) < 700 and
                    boss.phase == 1 and not self.dark_fairy_spell_list) or (random.randint(0, 80) == 0 and
                                                                            arcade.get_distance_between_sprites(
                                                                                self.seraphima,
                                                                                boss) < 400 and boss.phase == 2):
                    boss.is_casting = True
                    spell_x = self.seraphima.center_x + random.randint(-300, 300)
                    spell_y = self.seraphima.center_y + random.randint(-300, 300)
                    spell = darkfairy_spell.DarkFairySpell(spell_x, spell_y, s.BOSS_SCALING, boss)
                    distance = arcade.get_distance_between_sprites(spell, self.seraphima)
                    if distance > spell.min_spawn_distance:
                        self.dark_fairy_spell_list.append(spell)
                    else:
                        while distance <= spell.min_spawn_distance:
                            spell_x = self.seraphima.center_x + random.randint(-500, 500)
                            spell_y = self.seraphima.center_y + random.randint(-500, 500)
                            spell.center_x, spell.center_y = spell_x, spell_y
                            distance = arcade.get_distance_between_sprites(spell, self.seraphima)
                        self.dark_fairy_spell_list.append(spell)

        self.boss_list.update()
        if s.ghosts_killed % 15 == 0 and s.ghosts_killed != 0:
            self.spawn_boss()
            s.ghosts_killed += 1

    def update_music(self):
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
        for i in range(70):
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
                elif wall.collides_with_list(self.boss_list):
                    overlap = True
                    break
            if not overlap:
                if random.random() > 0.9:
                    wall.scale *= random.randint(50, 200) / 100
                    if random.random() > 0.95:
                        wall.scale *= random.randint(150, 400) / 100
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

    @staticmethod
    def handle_boss_damage(DarkFairy):
        DarkFairy.health -= 1
        DarkFairy.is_being_hurt = True

    def move_ghost(self, ghost):

        # If the player is out of bounds then the ghost will follow the player
        if self.seraphima.bottom < 80 or self.seraphima.left < 80:
            angle = math.atan2(self.seraphima.center_y - ghost.center_y,
                               self.seraphima.center_x - ghost.center_x)
            ghost.change_x = math.cos(angle) * s.MONSTER_MOVEMENT_SPEED
            ghost.change_y = math.sin(angle) * s.MONSTER_MOVEMENT_SPEED
            ghost.change_x += s.MONSTER_MOVEMENT_SPEED * ghost.change_x / abs(ghost.change_x)
            ghost.change_y += s.MONSTER_MOVEMENT_SPEED * ghost.change_y / abs(ghost.change_y)
            ghost.is_out_of_bounds = True

        # Make sure that the ghost doesn't try to follow the path into the side of the level
        # Instead, if they are beyond a certain bounds, just move towards the player
        elif ghost.bottom < 60 or ghost.left < 70:
            angle = math.atan2(self.seraphima.center_y - ghost.center_y,
                               self.seraphima.center_x - ghost.center_x)
            ghost.change_x = math.cos(angle) * s.MONSTER_MOVEMENT_SPEED
            ghost.change_y = math.sin(angle) * s.MONSTER_MOVEMENT_SPEED
            ghost.change_x += s.MONSTER_MOVEMENT_SPEED * ghost.change_x / abs(ghost.change_x)
            ghost.change_y += s.MONSTER_MOVEMENT_SPEED * ghost.change_y / abs(ghost.change_y)
            ghost.is_out_of_bounds = True

        # Otherwise the ghost will follow the path
        else:
            self.path = arcade.astar_calculate_path(ghost.position,
                                                    self.seraphima.position,
                                                    self.barrier_list,
                                                    diagonal_movement=False)
        if self.path and not self.is_dead and \
                arcade.get_distance_between_sprites(ghost, self.seraphima) < s.MONSTER_VISION_RANGE:
            if not ghost.is_hunting:
                ghost.is_hunting = True

            # Figure out where we want to go
            try:
                next_x = self.path[ghost.current_path_position][0]
                next_y = self.path[ghost.current_path_position][1]
            except IndexError:

                # We are at the end of the path
                next_x = self.seraphima.center_x
                next_y = self.seraphima.center_y

            # What's the difference between the two
            diff_x = next_x - ghost.center_x
            diff_y = next_y - ghost.center_y

            # What's our angle
            angle = math.atan2(diff_y, diff_x)

            # Calculate the travel vector
            ghost.change_x = math.cos(angle) * s.MONSTER_MOVEMENT_SPEED
            ghost.change_y = math.sin(angle) * s.MONSTER_MOVEMENT_SPEED
            if (ghost.change_y ** 2 + ghost.change_x ** 2) ** 0.5 > s.MONSTER_MOVEMENT_SPEED:
                ghost.change_x += s.MONSTER_MOVEMENT_SPEED * ghost.change_x / abs(ghost.change_x)
                ghost.change_y += s.MONSTER_MOVEMENT_SPEED * ghost.change_y / abs(ghost.change_y)

            # Recalculate distance after the move
            distance = math.sqrt((ghost.center_x - next_x) ** 2 + (ghost.center_y - next_y) ** 2)

            # If we're close enough, move to the next point
            if distance < s.MONSTER_MOVEMENT_SPEED:
                ghost.current_path_position += 1

                # If we're at the end of the path, start over
                if ghost.current_path_position >= len(self.path):
                    ghost.current_path_position = 0
        elif not ghost.is_out_of_bounds:
            if ghost.is_hunting:
                ghost.is_hunting = False

            # If we can't find a path, or are far enough away from the player just move randomly:
            if random.randint(0, 100) == 0:
                ghost.change_x = random.uniform(-s.MONSTER_MOVEMENT_SPEED, s.MONSTER_MOVEMENT_SPEED)
                ghost.change_y = random.uniform(-s.MONSTER_MOVEMENT_SPEED, s.MONSTER_MOVEMENT_SPEED)

        else:
            if ghost.is_hunting:
                ghost.is_hunting = False

    def move_spell(self, spell):
        if spell.change_x == 0 and spell.change_y == 0:
            angle = math.atan2(self.seraphima.center_y - spell.center_y,
                               self.seraphima.center_x - spell.center_x)
            spell.change_x = math.cos(angle) * s.SPELL_MOVEMENT_SPEED
            spell.change_y = math.sin(angle) * s.SPELL_MOVEMENT_SPEED
        elif spell.current_frame == int(len(spell.phase_1_frames) / 2):
            angle = math.atan2(self.seraphima.center_y - spell.center_y,
                               self.seraphima.center_x - spell.center_x)
            spell.change_x = math.cos(angle) * s.SPELL_MOVEMENT_SPEED
            spell.change_y = math.sin(angle) * s.SPELL_MOVEMENT_SPEED

    def move_boss(self):
        for boss in self.boss_list:
            if random.randint(0, 100) == 0:
                boss.change_x = random.randint(int(-s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier),
                                               int(s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier))
                boss.change_y = random.randint(int(-s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier),
                                               int(s.BOSS_MOVEMENT_SPEED * boss.movement_speed_modifier))

    def spawn_ghosts(self):
        for i in range(int(self.ghosts_to_spawn)):
            random_x = random.uniform(self.seraphima.center_x - 50, self.seraphima.center_x + 50)
            random_y = random.uniform(self.seraphima.center_y - 50, self.seraphima.center_y + 50)
            if random_x < 0 or random_x > self.level_map.width or random_y < 0 or \
                    random_y > self.level_map.height:
                random_x = random.uniform(0, self.width)
                random_y = random.uniform(0, self.height)
            ghost = g.GhostMonster(random_x, random_y, s.MONSTER_SCALING)
            ghost.texture = arcade.load_texture("assets/enemies/ghost/g_south-0.png")

            # Check if the new ghost collides with any existing ghosts, wall sprites or player
            collision = False
            for wall in self.wall_list:
                if ghost.collides_with_sprite(wall):
                    collision = True
                    break
            if ghost.collides_with_sprite(self.seraphima):
                collision = True
            if not collision:
                if random.random() > 0.95:
                    ghost.scale *= random.randint(80, 140) / 100
                self.ghost_list.append(ghost)
            else:

                # If there is a collision, Don't spawn the ghost and try again
                self.ghosts_to_spawn += 1

            # If there are too many ghosts, don't spawn more, instead increase the movement
            over_ghosts = len(self.ghost_list) - 25
            if over_ghosts > 0:
                for ghost in self.ghost_list:
                    if over_ghosts >= 0:
                        break
                    elif ghost.movement_speed_modifier < 1.9:
                        ghost.movement_speed_modifier += 0.1
                        over_ghosts -= 1
                    else:
                        over_ghosts -= 1
            if self.ghosts_to_spawn > 25:
                self.ghosts_to_spawn = 25

    def spawn_ghosts_on_empty_list(self):

        # Handle spawning in more ghosts if there aren't any on the screen, and it's been a few seconds
        if not self.ghost_list:
            if self.no_ghost_timer != 0:
                self.no_ghost_timer = time.time()
            elif time.time() - self.no_ghost_timer > 5:
                self.spawn_ghosts()

                # Reset the timer and increase the number of ghosts to spawn
                self.ghosts_to_spawn += 0.5
            self.ghosts_to_spawn *= self.ghosts_to_spawn_multiplier
            self.no_ghost_timer = 0.0

    def spawn_boss(self):
        for i in range(s.bosses_to_spawn):
            boss_x = self.seraphima.center_x + random.randint(-500, 500)
            boss_y = self.seraphima.center_y + random.randint(-500, 500)
            boss = darkfairy.DarkFairy(boss_x, boss_y, s.BOSS_SCALING)

            distance = arcade.get_distance_between_sprites(boss, self.seraphima)
            # Make the ghost move into the play area if they are outside it
            if distance > boss.min_spawn_distance and boss.left > 32 and boss.top < 2527 and \
                    boss.right < 2527 and boss.bottom > 32:
                self.boss_list.append(boss)
            else:
                while distance <= boss.min_spawn_distance or boss.left < 32 or boss.top > 2527 or \
                        boss.right > 2527 or boss.bottom < 32:
                    boss_x = self.seraphima.center_x + random.randint(-500, 500)
                    boss_y = self.seraphima.center_y + random.randint(-500, 500)
                    boss.center_x, boss.center_y = boss_x, boss_y
                    distance = arcade.get_distance_between_sprites(boss, self.seraphima)
                self.boss_list.append(boss)

    def scroll_to_player(self, speed=s.CAMERA_SPEED):
        position = Vec2(self.seraphima.center_x - self.width / 2,
                        self.seraphima.center_y - self.height / 2)
        self.camera.move_to(position, speed)

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


if __name__ == "__main__":
    window = MyGame(s.SCREEN_WIDTH, s.SCREEN_HEIGHT, s.SCREEN_TITLE)
    window.set_location(0, 30)
    arcade.run()
