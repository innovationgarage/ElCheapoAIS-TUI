from . import screen
from .utils import strw

class CatScreen(screen.DisplayScreen):
    def __init__(self, tui):
        self.tui = tui
        s = screen.empty_screen
        cat = r"""       _..---..,""-._     ,/}/)
    .''       ,      ``..'(/-<
   /   _     {      )         \
  ;   _ `.    `.   <         a(
 /   ( \  )     `.  \ __.._ .: y
( <\_-) )'-.___...\  `._   //-'
 \ `-' /-._))      `-._)))
  `...'
"""
        for idx, line in enumerate(cat.split("\n")):
            s = strw(s, 1, idx+1, line)
        
        screen.DisplayScreen.__init__(self, s)

    def action_0(self):
        return self.tui.main_screen
    def action_1(self):
        return self.tui.main_screen
    def action_2(self):
        return self.tui.main_screen
