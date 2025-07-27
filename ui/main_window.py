import os
import gi
import markdown2

from ui.note_handler import NoteHandler

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
gi.require_version("GtkSource", "4")
from gi.repository import Gtk, WebKit2, GtkSource, GLib, GdkPixbuf

NOTES_DIR = "notes"


class BropadWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Bropad", default_width=1000, default_height=600)
        self.set_border_width(0)

        os.makedirs(NOTES_DIR, exist_ok=True)
        self.handler = NoteHandler(NOTES_DIR)

        self.notes_list = Gtk.ListBox()
        self.notes_list.connect("row-selected", self.on_note_selected)
        self.notes_list.connect("button-press-event", self.on_listbox_right_click)
        self.load_notes()

        self.text_buffer = GtkSource.Buffer()
        self.text_buffer.connect("changed", self.update_preview)
        self.text_view = GtkSource.View.new_with_buffer(self.text_buffer)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_show_line_numbers(False)
        self.line_numbers_visible = False

        self.web_view = WebKit2.WebView()
        self.preview_scrolled = Gtk.ScrolledWindow()
        self.preview_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.preview_scrolled.add(self.web_view)
        self.preview_scrolled.set_visible(False)
        self.preview_visible = False

        # Tambah note (ikon + tooltip)
        self.btn_new = Gtk.Button()
        self.btn_new.set_image(Gtk.Image.new_from_icon_name("document-new", Gtk.IconSize.BUTTON))
        self.btn_new.set_tooltip_text("New Note")
        self.btn_new.connect("clicked", self.on_new_note)

        # Simpan note
        self.btn_save = Gtk.Button()
        self.btn_save.set_image(Gtk.Image.new_from_icon_name("document-save", Gtk.IconSize.BUTTON))
        self.btn_save.set_tooltip_text("Save Note")
        self.btn_save.connect("clicked", self.on_save_note)

        # Toggle preview
        self.btn_toggle_preview = Gtk.Button()
        self.btn_toggle_preview.set_image(Gtk.Image.new_from_icon_name("view-preview", Gtk.IconSize.BUTTON))
        self.btn_toggle_preview.set_tooltip_text("Toggle Preview")
        self.btn_toggle_preview.connect("clicked", self.on_toggle_preview)

        # Toggle line number
        self.btn_toggle_lines = Gtk.Button()
        self.btn_toggle_lines.set_image(Gtk.Image.new_from_icon_name("accessories-text-editor", Gtk.IconSize.BUTTON))
        self.btn_toggle_lines.set_tooltip_text("Toggle Line Numbers")
        self.btn_toggle_lines.connect("clicked", self.on_toggle_line_numbers)

        menubar = Gtk.MenuBar()

        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.on_quit)
        file_menu.append(quit_item)
        file_item.set_submenu(file_menu)

        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Help")
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self.on_about)
        help_menu.append(about_item)
        help_item.set_submenu(help_menu)

        menubar.append(file_item)
        menubar.append(help_item)

        btn_box = Gtk.Box(spacing=6)
        btn_box.pack_start(self.btn_new, False, False, 0)
        btn_box.pack_start(self.btn_save, False, False, 0)
        btn_box.pack_start(self.btn_toggle_preview, False, False, 0)
        btn_box.pack_start(self.btn_toggle_lines, False, False, 0)

        left_scrolled = Gtk.ScrolledWindow()
        left_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        left_scrolled.add(self.notes_list)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.pack_start(Gtk.Label(label="🗂️ Notes", xalign=0), False, False, 0)
        left.pack_start(left_scrolled, True, True, 0)

        self.editor_preview_pane = Gtk.Paned()
        self.editor_preview_pane.set_wide_handle(True)

        editor_scrolled = Gtk.ScrolledWindow()
        editor_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        editor_scrolled.add(self.text_view)

        self.editor_preview_pane.pack1(editor_scrolled, True, False)
        self.editor_preview_pane.pack2(self.preview_scrolled, True, False)

        main_pane = Gtk.Paned()
        main_pane.set_wide_handle(True)
        main_pane.add1(left)
        main_pane.add2(self.editor_preview_pane)

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        layout.pack_start(menubar, False, False, 0)
        layout.pack_start(btn_box, False, False, 5)
        layout.pack_start(main_pane, True, True, 5)

        self.add(layout)
        self.show_all()
        self.preview_scrolled.set_visible(False)

        self.current_filename = None

    def load_notes(self):
        self.notes_list.foreach(lambda row: self.notes_list.remove(row))
        for filename in sorted(os.listdir(NOTES_DIR)):
            if filename.endswith(".md"):
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                icon = Gtk.Image.new_from_icon_name("text-x-markdown", Gtk.IconSize.MENU)
                if not icon.get_storage_type():
                    icon = Gtk.Image.new_from_icon_name("text-plain", Gtk.IconSize.MENU)
                label = Gtk.Label(label=filename, xalign=0)
                hbox.pack_start(icon, False, False, 0)
                hbox.pack_start(label, True, True, 0)
                row = Gtk.ListBoxRow()
                row.add(hbox)
                self.notes_list.add(row)
        self.notes_list.show_all()

    def on_note_selected(self, listbox, row):
        if not row:
            return
        hbox = row.get_child()
        label = hbox.get_children()[1]
        filename = label.get_text()
        content = self.handler.load_note(filename)
        self.text_buffer.set_text(content)
        self.current_filename = filename
        self.update_preview()

    def on_new_note(self, _):
        self.text_buffer.set_text("")
        self.current_filename = self.handler.create_new_note()
        self.load_notes()
        self.update_preview()

    def on_save_note(self, _):
        if not self.current_filename:
            return
        start, end = self.text_buffer.get_bounds()
        content = self.text_buffer.get_text(start, end, True)
        self.handler.save_note(self.current_filename, content)
        self.update_preview()

    def on_quit(self, _):
        self.get_application().quit()

    def on_about(self, _):
        dialog = Gtk.Dialog(
            title="About Bropad",
            transient_for=self,
            flags=0,
        )
        dialog.add_button("OK", Gtk.ResponseType.OK)
        dialog.set_default_size(400, 400)

        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)
        content_area.set_margin_start(20)
        content_area.set_margin_end(20)

        # === Logo dan Deskripsi (atas) ===
        vbox_top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox_top.set_halign(Gtk.Align.CENTER)

        logo_path = os.path.abspath(os.path.join("assets", "logo.png"))
        if os.path.exists(logo_path):
            try:
                from gi.repository import GdkPixbuf
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    filename=logo_path,
                    width=96,
                    height=96,
                    preserve_aspect_ratio=True,
                )
                image = Gtk.Image.new_from_pixbuf(pixbuf)
                vbox_top.pack_start(image, False, False, 0)
            except Exception as e:
                print(f"Gagal load logo: {e}")

        label = Gtk.Label(label="Bropad - Markdown Note Editor\nVersi 1.0\n\nBuilt with ♥ using GTK + Python")
        label.set_justify(Gtk.Justification.CENTER)
        label.set_halign(Gtk.Align.CENTER)
        vbox_top.pack_start(label, False, False, 0)

        content_area.add(vbox_top)

        # === Notebook (tab) ===
        notebook = Gtk.Notebook()
        notebook.set_hexpand(True)
        notebook.set_vexpand(True)

        # Tab 1: License
        license_path = os.path.abspath(os.path.join("LICENSE"))
        try:
            with open(license_path, "r") as f:
                license_text = f.read()
        except Exception as e:
            license_text = f"Gagal membaca file LICENSE:\n{e}"

        license_view = Gtk.TextView()
        license_view.set_margin_top(10)
        license_view.set_margin_start(10)
        license_view.set_margin_end(10)
        license_view.set_editable(False)
        license_view.set_cursor_visible(False)
        license_view.set_wrap_mode(Gtk.WrapMode.NONE)

        buffer = license_view.get_buffer()
        buffer.set_text(license_text)

        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(license_view)

        notebook.append_page(scroll, Gtk.Label(label="Lisensi"))

        # Tab 2: Contributors
        contributors_label = Gtk.Label(label="""
Kontributor:
- Angga Purnama (anggagewor@gmail.com)

Terima kasih juga buat komunitas Python + GTK!
""")
        contributors_label.set_xalign(0)
        contributors_label.set_yalign(0)
        contributors_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        contributors_box.set_margin_top(10)
        contributors_box.set_margin_start(10)
        contributors_box.set_margin_end(10)
        contributors_box.pack_start(contributors_label, True, True, 0)
        notebook.append_page(contributors_box, Gtk.Label(label="Kontributor"))

        content_area.add(notebook)

        dialog.show_all()
        dialog.run()
        dialog.destroy()


    def update_preview(self, *_):
        start, end = self.text_buffer.get_bounds()
        raw_text = self.text_buffer.get_text(start, end, True)
        html = markdown2.markdown(raw_text, extras=[
            "fenced-code-blocks",
            "code-friendly",
            "tables",
            "cuddled-lists",
            "footnotes",
            "strike",
            "header-ids",
            "markdown-in-html",
            "task_list",
        ])
        styled = f"<html><body style='font-family: sans-serif; padding:20px'>{html}</body></html>"
        self.web_view.load_html(styled, "file:///")

    def on_toggle_preview(self, button):
        self.preview_visible = not self.preview_visible
        self.preview_scrolled.set_visible(self.preview_visible)
        if self.preview_visible:
            self.update_preview()

    def on_toggle_line_numbers(self, button):
        self.line_numbers_visible = not self.line_numbers_visible
        self.text_view.set_show_line_numbers(self.line_numbers_visible)

    def on_listbox_right_click(self, widget, event):
        if event.button != 3:
            return
        row = widget.get_row_at_y(event.y)
        if not row:
            return
        menu = Gtk.Menu()
        rename_item = Gtk.MenuItem(label="✏️ Rename")
        delete_item = Gtk.MenuItem(label="🗑️ Delete")
        rename_item.connect("activate", self.on_rename_note, row)
        delete_item.connect("activate", self.on_delete_note, row)
        menu.append(rename_item)
        menu.append(delete_item)
        menu.show_all()
        menu.popup_at_pointer(event)
        return True

    def on_rename_note(self, menuitem, row):
        hbox = row.get_child()
        label = hbox.get_children()[1]
        old_filename = label.get_text()

        dialog = Gtk.Dialog(
            title="Rename Note",
            transient_for=self,
            flags=0,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Rename", Gtk.ResponseType.OK)

        entry = Gtk.Entry()
        entry.set_text(old_filename)
        box = dialog.get_content_area()
        box.add(Gtk.Label(label="New filename:"))
        box.add(entry)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_filename = entry.get_text()
            if new_filename != old_filename:
                if not new_filename.endswith(".md"):
                    new_filename += ".md"
                old_path = os.path.join(NOTES_DIR, old_filename)
                new_path = os.path.join(NOTES_DIR, new_filename)
                if os.path.exists(new_path):
                    self._show_message("Filename already exists!")
                else:
                    os.rename(old_path, new_path)
                    if self.current_filename == old_filename:
                        self.current_filename = new_filename
                    self.load_notes()
        dialog.destroy()

    def on_delete_note(self, menuitem, row):
        hbox = row.get_child()
        label = hbox.get_children()[1]
        filename = label.get_text()

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete '{filename}'?",
        )
        dialog.format_secondary_text("This action cannot be undone.")
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            file_path = os.path.join(NOTES_DIR, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                if self.current_filename == filename:
                    self.text_buffer.set_text("")
                    self.current_filename = None
                self.load_notes()

    def _show_message(self, text):
        msg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=text,
        )
        msg.run()
        msg.destroy()
