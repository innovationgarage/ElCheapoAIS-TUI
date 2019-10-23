from . import screen
import os.path

class DirectoryScreen(screen.Menu):
    def __init__(self, tui):
        self.tui = tui
        screen.Menu.__init__(self, [])
        self.cd()
        
    def cd(self, path = '/'):
        self.path = path
        try:
            entries = os.listdir(path)
        except Exception as e:
            self.entries = ["..", "<%s>" % (e,)]
        else:
            dirs = []
            files = []
            for entry in entries:
                if os.path.isdir(os.path.join(self.path, entry)):
                    dirs.append(entry)
                else:
                    files.append(entry)
            dirs.sort()
            files.sort()
            self.entries = [".."] + dirs + files
        self["title"] = path
        self.pos = 0

    def action(self, entry):
        entry = self.entries[entry]
        if entry == "..":
            if self.path == "/":
                return self.tui.debug_screen
            else:
                self.cd(os.path.split(self.path)[0])
                return self
        else:
            entrypath = os.path.join(self.path, entry)
            if os.path.isdir(entrypath):
                self.cd(os.path.join(self.path, entry))
                return self
            else:
                self.tui.file_screen.open(entrypath)
                return self.tui.file_screen
    
class FileScreen(screen.TextScroll):
    def __init__(self, tui):
        self.tui = tui
        screen.TextScroll.__init__(self, "")

    def open(self, filename):
        try:
            with open(filename) as f:
                content = f.read()
            self.set_content(content.replace(": ", ":\n"))
        except Exception as e:
            self.set_content("<%s>" % (e,))
            
    def action(self, value):
        return self.tui.directory_screen
