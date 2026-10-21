#!/usr/bin/env python3

import gi
import os
import subprocess
import threading
import time
import argparse
from datetime import datetime
from PIL import Image
import pytesseract

gi.require_version("Gtk", "4.0")
gi.require_version("Xdp", "1.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, GLib, Xdp, Gdk, Adw, GObject, Gio

class TextDialog(Gtk.Dialog):
    def __init__(self, app, text=""):
        super().__init__(title="Extracted Text", application=app, modal=True)
        self.app = app
        self.set_default_size(600, 450)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(box)

        scrolled_window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.text_view = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD, margin_start=12, margin_end=12, margin_top=12)
        self.text_view.get_buffer().set_text(text)
        scrolled_window.set_child(self.text_view)
        box.append(scrolled_window)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, margin_bottom=12, margin_start=12, margin_end=12, homogeneous=True)
        
        btn_save = Gtk.Button(label="Save to File")
        btn_copy = Gtk.Button(label="Copy to Clipboard")
        self.btn_speak = Gtk.Button(label="Speak")
        btn_retake = Gtk.Button(label="Retake Screenshot")

        self.speak_state = "idle"

        btn_save.connect("clicked", self.on_save_clicked)
        btn_copy.connect("clicked", self.on_copy_clicked)
        self.btn_speak.connect("clicked", self.on_speak_clicked)
        btn_retake.connect("clicked", self.on_take_another_clicked)

        button_box.append(btn_save)
        button_box.append(btn_copy)
        button_box.append(self.btn_speak)
        button_box.append(btn_retake)
        box.append(button_box)
        self.present()

    def get_text(self):
        buffer = self.text_view.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)

    def on_save_clicked(self, button):
        dialog = Gtk.FileDialog(title="Save Extracted Text")
        dialog.set_initial_name(f"ocr_{datetime.now().strftime('%H-%M')}.txt")
        dialog.save(parent=self, cancellable=None, callback=self._on_save_response)

    def _on_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                with open(file.get_path(), "w") as f:
                    f.write(self.get_text())
                if not self.app.no_close_on_action: self.app.quit()
        except: pass

    def on_copy_clicked(self, button):
        self.get_clipboard().set_content(Gdk.ContentProvider.new_for_value(self.get_text()))
        GLib.timeout_add(50, self.app.quit)

    def on_take_another_clicked(self, button):
        self.destroy()
        # Increased to allow GNOME window animations to finish
        GLib.timeout_add(600, self.app.take_screenshot)

    def on_speak_clicked(self, button):
        if self.speak_state == "idle":
            self.speak_state = "playing"
            self.btn_speak.set_label("Pause")
            threading.Thread(target=self.run_speech_thread, args=(self.get_text(),), daemon=True).start()
        elif self.speak_state == "playing":
            subprocess.run("killall -STOP pw-play 2>/dev/null", shell=True)
            self.speak_state = "paused"; self.btn_speak.set_label("Resume")
        elif self.speak_state == "paused":
            subprocess.run("killall -CONT pw-play 2>/dev/null", shell=True)
            self.speak_state = "playing"; self.btn_speak.set_label("Pause")

    def run_speech_thread(self, text):
        subprocess.run(["spd-say", "-C"])
        subprocess.run(["spd-say", text])
        
        # Phase 1: Wait for process to start
        player_detected = False
        for _ in range(50):
            if subprocess.run("pgrep -f 'pw-play /tmp/piper_tts.wav'", shell=True, capture_output=True).returncode == 0:
                player_detected = True
                break
            time.sleep(0.1)
        
        # Phase 2: Watch until process exits
        if player_detected:
            while True:
                if subprocess.run("pgrep -f 'pw-play /tmp/piper_tts.wav'", shell=True, capture_output=True).returncode != 0:
                    time.sleep(0.5)
                    if subprocess.run("pgrep -f 'pw-play /tmp/piper_tts.wav'", shell=True, capture_output=True).returncode != 0: 
                        break
                time.sleep(0.5)
            
        GLib.idle_add(self.reset_speak_button)

    def reset_speak_button(self):
        self.speak_state = "idle"
        self.btn_speak.set_label("Speak")
        return False

class GnomeOCRApp(Gtk.Application):
    def __init__(self, lang=None):
        super().__init__(); self.portal = Xdp.Portal(); self.lang = lang
        self.no_close_on_action = False

    def do_activate(self):
        self.win = Gtk.ApplicationWindow(application=self, opacity=0)
        self.win.present(); GLib.timeout_add(100, self.take_screenshot)

    def take_screenshot(self):
        self.portal.take_screenshot(None, Xdp.ScreenshotFlags.INTERACTIVE, None, self.on_screenshot_taken, None)
        return False

    def on_screenshot_taken(self, source_object, res, user_data):
        try:
            filename = GLib.Uri.unescape_string(self.portal.take_screenshot_finish(res)[7:])
            text = pytesseract.image_to_string(Image.open(filename), lang=self.lang)
            if text:
                dialog = TextDialog(self, text)
                dialog.connect("close-request", self.on_dialog_close)
                dialog.present()
            os.unlink(filename)
        except: self.quit()

    def on_dialog_close(self, dialog):
        subprocess.run("spd-say -C", shell=True)
        subprocess.run("killall -CONT pw-play 2>/dev/null", shell=True)
        subprocess.run("killall -9 pw-play 2>/dev/null", shell=True)
        dialog.destroy(); self.quit()

parser = argparse.ArgumentParser(); parser.add_argument("--lang", action="store")
args = parser.parse_args(); app = GnomeOCRApp(lang=args.lang); app.run(None)
