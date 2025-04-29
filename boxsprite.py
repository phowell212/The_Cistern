import arcade

class BoxSprite(arcade.Sprite):
    def __init__(self, center_x, center_y,
                 width=20000, height=20000):
        super().__init__()
        self.center_x = center_x
        self.center_y = center_y
        self.width    = width
        self.height   = height
        self.texture  = arcade.load_texture("assets/background.png")
