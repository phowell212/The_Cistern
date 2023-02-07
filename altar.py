import arcade
import settings as s


class Altar(arcade.Sprite):
    def __init__(self, center_x, center_y):
        super().__init__()
        self.center_x = center_x
        self.center_y = center_y
        self.texture = arcade.load_texture("assets/altar/pentagram2-0.png")
        self.scale = s.ALTAR_SCALING
        self.frames = []
        self.load_frames()
        self.current_frame = 0
        self.elapsed_time = 0
        self.update_interval = 1 / 10

    def update_animation(self, delta_time: float = 1 / 60):
        self.elapsed_time += delta_time
        if self.elapsed_time > self.update_interval:
            self.elapsed_time = 0
            self.current_frame += 1

        try:
            self.texture = self.frames[int(self.current_frame)]
        except IndexError:
            self.current_frame = 0
            self.texture = self.frames[int(self.current_frame)]

    def load_frames(self):
        for i in range(0, 12):
            self.frames.append(arcade.load_texture(f"assets/altar/pentagram2-{i}.png"))
