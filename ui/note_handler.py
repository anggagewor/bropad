import os
from datetime import datetime


class NoteHandler:
    def __init__(self, notes_dir):
        self.notes_dir = notes_dir

    def get_note_path(self, filename):
        return os.path.join(self.notes_dir, filename)

    def load_note(self, filename):
        path = self.get_note_path(filename)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def save_note(self, filename, content):
        path = self.get_note_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def create_new_note(self):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        filename = f"{timestamp}.md"
        path = self.get_note_path(filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# New Note\n\n")
        return filename
