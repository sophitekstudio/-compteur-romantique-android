"""
Compteur Romantique v3 — Sophitek Studio (édition Kivy / Android)
Développé par Japhet Arcade Sophiano ASSOGBA
Portage de la version PyQt6 vers Kivy pour compilation Android (.apk)
"""

import os
import json
import math
import random
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle, PushMatrix, PopMatrix, Rotate
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import StringProperty, DictProperty
from kivy.metrics import dp
from dateutil.relativedelta import relativedelta

# ═══════════════════════════════════════════════════════════════════════════════
#  CHEMINS
# ═══════════════════════════════════════════════════════════════════════════════
def resource_path(*parts):
    """Ressource en lecture seule, bundlée avec l'app (assets/...)."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)

FONT_PATH  = resource_path("assets", "fonts", "futura.ttf")
HEART_PATH = resource_path("assets", "images", "heart.png")
MUSIC_PATH = resource_path("assets", "music", "fond.mp3")

# ═══════════════════════════════════════════════════════════════════════════════
#  COULEURS (format Kivy : 0..1 au lieu de 0..255)
# ═══════════════════════════════════════════════════════════════════════════════
def hexcol(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    return (r, g, b, a)

C_BG      = hexcol("0d0818")
C_PINK    = hexcol("FFB6C1")
C_ROSE    = hexcol("FF6482")
C_GOLD    = hexcol("FFD700")
C_TEXT    = hexcol("FFE0EA")
C_BTN_TXT = hexcol("321428")

# ═══════════════════════════════════════════════════════════════════════════════
#  POLICE
# ═══════════════════════════════════════════════════════════════════════════════
FONT_NAME = "Roboto"  # police système par défaut si le fichier custom manque
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name="Futura", fn_regular=FONT_PATH)
        FONT_NAME = "Futura"
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG PERSISTANTE
#  On utilise le dossier de données propre à l'app fourni par Kivy :
#  - Windows  : %APPDATA%\<AppName>
#  - Android  : stockage privé de l'app (toujours accessible en écriture,
#               survit aux mises à jour, pas de permission nécessaire)
#  - Linux    : ~/.config/<AppName>
#  Résout définitivement le problème de sauvegarde qui "disparaît".
# ═══════════════════════════════════════════════════════════════════════════════
def get_config_path():
    app = App.get_running_app()
    d = app.user_data_dir if app else "."
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "countdown_config.json")

def load_config() -> dict:
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"events": [], "footer_text": "Chaque seconde me rapproche de toi 💖"}

def save_config(cfg: dict):
    try:
        with open(get_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[save_config] {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#  FORMATAGE TEMPS (logique identique à la version PyQt, en local naive time)
# ═══════════════════════════════════════════════════════════════════════════════
def fmt_delta(dt_from: datetime, dt_to: datetime) -> str:
    if dt_to <= dt_from:
        return "00h:00m:00s"
    rd = relativedelta(dt_to, dt_from)
    y, mo, d = rd.years, rd.months, rd.days
    w, rd2 = d // 7, d % 7
    ts = int((dt_to - dt_from).total_seconds())
    h = (ts % 86400) // 3600
    m = (ts % 3600) // 60
    s = ts % 60
    parts = []
    if y:   parts.append(f"{y} an{'s' if y > 1 else ''}")
    if mo:  parts.append(f"{mo} mois")
    if w:   parts.append(f"{w} sem")
    if rd2: parts.append(f"{rd2}j")
    parts.append(f"{h:02d}h:{m:02d}m:{s:02d}s")
    return "  ".join(parts)

def next_anniv(origin: datetime, now: datetime) -> datetime:
    try:
        c = origin.replace(year=now.year)
    except ValueError:
        c = origin.replace(year=now.year, day=28)
    if c <= now:
        try:
            c = origin.replace(year=now.year + 1)
        except ValueError:
            c = origin.replace(year=now.year + 1, day=28)
    return c

def parse_date(raw: str):
    """Tolère les anciens fichiers de config qui contiennent un fuseau horaire
    (ancienne version PyQt), et les nouvelles entrées naive (locales)."""
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
#  FOND ANIMÉ : cœurs / étoiles / neige / points de vague
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ("kind", "w", "h", "x", "y", "size", "speed", "alpha",
                 "drift", "angle", "rot_speed", "phase")

    def __init__(self, kind, w, h):
        self.kind = kind
        self.w, self.h = w, h
        self._reset(initial=True)

    def _reset(self, initial=False):
        self.x = random.uniform(0, self.w)
        self.y = random.uniform(0, self.h) if initial else -random.uniform(0, self.h * 0.3)
        self.size = random.uniform(dp(6), dp(16))
        self.speed = random.uniform(dp(0.4), dp(1.2))
        self.alpha = random.uniform(0.25, 0.75)
        self.drift = random.uniform(-0.4, 0.4)
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-1.2, 1.2)
        self.phase = random.uniform(0, math.pi * 2)

    def update(self, tick):
        self.y += self.speed
        self.x += self.drift + math.sin(tick * 0.02 + self.phase) * 0.4
        self.angle += self.rot_speed
        if self.y > self.h + self.size * 2:
            self._reset()


class ParticleBackground(Widget):
    """Fond animé transparent, dessiné en Canvas, placé derrière le ScreenManager."""
    N_PARTICLES = 45

    def __init__(self, **kw):
        super().__init__(**kw)
        self._particles = []
        self._tick = 0
        self._wave_offset = 0.0
        self._heart_img = HEART_PATH if os.path.exists(HEART_PATH) else None
        self.bind(size=self._on_resize, pos=self._on_resize)
        Clock.schedule_once(lambda dt: self._init_particles(), 0)
        Clock.schedule_interval(self._step, 1 / 30)

    def _init_particles(self):
        kinds = ["heart", "star", "snow", "wave_dot"]
        w = max(self.width, dp(360))
        h = max(self.height, dp(600))
        self._particles = [Particle(kinds[i % 4], w, h) for i in range(self.N_PARTICLES)]

    def _on_resize(self, *_):
        for pt in self._particles:
            pt.w, pt.h = self.width, self.height

    def _step(self, dt):
        self._tick += 1
        self._wave_offset += 0.03
        for pt in self._particles:
            pt.update(self._tick)
        self._draw()

    def _heart_points(self, cx, cy, s):
        """Approxime un cœur avec une petite polyligne (léger, portable)."""
        pts = []
        steps = 20
        for i in range(steps + 1):
            t = math.pi * 2 * i / steps
            x = 16 * math.sin(t) ** 3
            y = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
            pts += [cx + x * (s / 16), cy + y * (s / 16)]
        return pts

    def _star_points(self, cx, cy, s):
        pts = []
        r1, r2 = s * 0.5, s * 0.2
        for i in range(5):
            a1 = math.radians(i * 72 - 90)
            a2 = math.radians(i * 72 + 36 - 90)
            pts += [cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)]
            pts += [cx + r2 * math.cos(a2), cy + r2 * math.sin(a2)]
        pts += pts[:2]
        return pts

    def _draw(self):
        self.canvas.clear()
        W, H = self.width, self.height
        with self.canvas:
            # Fond sombre
            Color(*C_BG)
            Rectangle(pos=self.pos, size=self.size)

            # Image cœur en fond, très transparente
            if self._heart_img:
                Color(1, 1, 1, 0.10)
                side = max(W, H) * 1.1
                Rectangle(source=self._heart_img,
                          pos=(self.x + (W - side) / 2, self.y + (H - side) / 2),
                          size=(side, side))

            # Voile sombre par-dessus (simule le dégradé de la version PyQt)
            Color(0.05, 0.03, 0.09, 0.55)
            Rectangle(pos=self.pos, size=self.size)

            # Vagues lumineuses en bas
            Color(0.78, 0.31, 0.55, 0.18)
            for wi in range(3):
                phase = self._wave_offset + wi * 1.1
                y0 = self.y + dp(40) + wi * dp(16)
                pts = []
                x = 0
                step = dp(8)
                while x < W + step:
                    yw = y0 + math.sin(x * 0.012 + phase) * dp(10)
                    pts += [self.x + x, yw]
                    x += step
                if len(pts) >= 4:
                    Line(points=pts, width=dp(1.2))

            # Particules
            for pt in self._particles:
                a = pt.alpha
                cx, cy = self.x + pt.x, self.y + pt.y
                if pt.kind == "heart":
                    Color(1.0, 0.31, 0.47, a)
                    Line(points=self._heart_points(cx, cy, pt.size), width=dp(1.3), close=True)
                elif pt.kind == "star":
                    Color(1.0, 0.84, 0.0, a)
                    Line(points=self._star_points(cx, cy, pt.size), width=dp(1.0), close=True)
                elif pt.kind == "snow":
                    Color(1.0, 0.78, 0.82, a)
                    r = pt.size * 0.3
                    Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
                else:  # wave_dot
                    Color(0.78, 0.39, 0.70, a * 0.6)
                    r = pt.size * 0.22
                    Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))


# ═══════════════════════════════════════════════════════════════════════════════
#  CARTE ÉVÉNEMENT (utilisée dans l'écran Compteurs)
# ═══════════════════════════════════════════════════════════════════════════════
class EventCard(BoxLayout):
    ev_name = StringProperty("")
    ev_main = StringProperty("")
    ev_next = StringProperty("")

    def __init__(self, event: dict, on_edit=None, on_delete=None, **kw):
        super().__init__(**kw)
        self.event = dict(event)
        self.on_edit_cb = on_edit
        self.on_delete_cb = on_delete
        self._refresh()
        self._clock = Clock.schedule_interval(lambda dt: self._refresh(), 1)

    def stop(self):
        if self._clock:
            self._clock.cancel()

    def update_event(self, ev: dict):
        self.event = dict(ev)
        self._refresh()

    def _refresh(self):
        ev = self.event
        now = datetime.now()
        etype = ev.get("type", "countdown")
        show_e = ev.get("show_elapsed", True)
        show_r = ev.get("show_remaining", True)
        self.ev_name = ev.get("name", "")
        self.ev_next = ""

        ev_dt = parse_date(ev.get("date", ""))
        if ev_dt is None:
            self.ev_main = "⚠ Date invalide"
            return

        lines = []
        if etype == "countdown":
            if show_r:
                if ev_dt > now:
                    lines.append(f"⏳ Dans :   {fmt_delta(now, ev_dt)}")
                else:
                    lines.append(f"✅ Passé depuis :   {fmt_delta(ev_dt, now)}")
        else:  # countup
            if show_e:
                if ev_dt <= now:
                    lines.append(f"💑 Ensemble depuis :   {fmt_delta(ev_dt, now)}")
                else:
                    lines.append(f"⏳ Commence dans :   {fmt_delta(now, ev_dt)}")
            if show_r:
                nxt = next_anniv(ev_dt, now)
                lines.append(f"🎉 Prochain anniversaire dans :   {fmt_delta(now, nxt)}")
                self.ev_next = f"📅 {nxt.strftime('%d/%m/%Y')}"
        self.ev_main = "\n".join(lines)

    def do_edit(self):
        if self.on_edit_cb:
            self.on_edit_cb(self.event)

    def do_delete(self):
        if self.on_delete_cb:
            self.on_delete_cb(self.event.get("name", ""))


# ═══════════════════════════════════════════════════════════════════════════════
#  POPUP CONFIRMATION
# ═══════════════════════════════════════════════════════════════════════════════
def confirm_popup(title, message, on_yes):
    content = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))
    content.add_widget(Label(text=message, color=C_TEXT, font_name=FONT_NAME))
    row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
    btn_yes = ButtonPink(text="Oui, supprimer")
    btn_no = ButtonGhost(text="Annuler")
    row.add_widget(btn_no)
    row.add_widget(btn_yes)
    content.add_widget(row)
    popup = Popup(title=title, content=content, size_hint=(0.8, 0.35))
    btn_no.bind(on_release=lambda *_: popup.dismiss())

    def _yes(*_):
        popup.dismiss()
        on_yes()
    btn_yes.bind(on_release=_yes)
    popup.open()


def info_popup(title, message):
    content = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))
    content.add_widget(Label(text=message, color=C_TEXT, font_name=FONT_NAME))
    btn = ButtonPink(text="OK", size_hint_y=None, height=dp(44))
    content.add_widget(btn)
    popup = Popup(title=title, content=content, size_hint=(0.8, 0.32))
    btn.bind(on_release=lambda *_: popup.dismiss())
    popup.open()


# ═══════════════════════════════════════════════════════════════════════════════
#  POPUP AJOUT / MODIFICATION D'ÉVÉNEMENT
# ═══════════════════════════════════════════════════════════════════════════════
class EventFormPopup(Popup):
    def __init__(self, config, event=None, on_saved=None, **kw):
        self.config = config
        self.editing_event = event
        self.on_saved = on_saved
        super().__init__(**kw)
        self.title = "✏ Modifier l'événement" if event else "💖 Nouvel événement"
        self.size_hint = (0.92, 0.85)
        self._build(event)

    def _build(self, event):
        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))

        root.add_widget(Label(text="Nom de l'événement :", color=C_PINK, size_hint_y=None,
                               height=dp(24), font_name=FONT_NAME, halign="left"))
        from kivy.uix.textinput import TextInput
        self.inp_name = TextInput(
            text=event.get("name", "") if event else "",
            multiline=False, size_hint_y=None, height=dp(42),
            readonly=bool(event), font_name=FONT_NAME)
        root.add_widget(self.inp_name)

        root.add_widget(Label(text="Date et heure (AAAA-MM-JJ HH:MM:SS) :", color=C_PINK,
                               size_hint_y=None, height=dp(24), font_name=FONT_NAME))
        date_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        default_dt = event.get("date") if event else None
        default_dt = parse_date(default_dt) if default_dt else datetime.now()
        default_dt = default_dt or datetime.now()
        self.inp_date = TextInput(
            text=default_dt.strftime("%Y-%m-%d %H:%M:%S"),
            multiline=False, font_name=FONT_NAME)
        btn_now = ButtonGhost(text="Maintenant", size_hint_x=None, width=dp(110))
        btn_now.bind(on_release=lambda *_: setattr(
            self.inp_date, "text", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        date_row.add_widget(self.inp_date)
        date_row.add_widget(btn_now)
        root.add_widget(date_row)

        root.add_widget(Label(text="Type :", color=C_PINK, size_hint_y=None,
                               height=dp(24), font_name=FONT_NAME))
        type_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.btn_countdown = ButtonToggle(text="⬇ Compte à rebours", group="ev_type")
        self.btn_countup = ButtonToggle(text="⬆ Temps écoulé", group="ev_type")
        is_countup = event and event.get("type") == "countup"
        self.btn_countdown.state = "normal" if is_countup else "down"
        self.btn_countup.state = "down" if is_countup else "normal"
        self.btn_countdown.bind(on_release=lambda *_: self._set_type(False))
        self.btn_countup.bind(on_release=lambda *_: self._set_type(True))
        type_row.add_widget(self.btn_countdown)
        type_row.add_widget(self.btn_countup)
        root.add_widget(type_row)

        from kivy.uix.checkbox import CheckBox
        chk_row1 = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self.chk_e = CheckBox(active=event.get("show_elapsed", True) if event else True,
                               size_hint_x=None, width=dp(34))
        chk_row1.add_widget(self.chk_e)
        chk_row1.add_widget(Label(text="⏱ Temps écoulé", color=C_TEXT, font_name=FONT_NAME,
                                   halign="left", valign="middle"))
        root.add_widget(chk_row1)

        chk_row2 = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self.chk_r = CheckBox(active=event.get("show_remaining", True) if event else True,
                               size_hint_x=None, width=dp(34))
        chk_row2.add_widget(self.chk_r)
        chk_row2.add_widget(Label(text="⏳ Temps restant / prochain anniversaire",
                                   color=C_TEXT, font_name=FONT_NAME, halign="left", valign="middle"))
        root.add_widget(chk_row2)

        self.lbl_status = Label(text="", color=(1, 0.3, 0.3, 1), size_hint_y=None,
                                 height=dp(24), font_name=FONT_NAME)
        root.add_widget(self.lbl_status)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        btn_cancel = ButtonGhost(text="Annuler")
        btn_save = ButtonPink(text="✔ Enregistrer")
        btn_cancel.bind(on_release=lambda *_: self.dismiss())
        btn_save.bind(on_release=lambda *_: self._save())
        btn_row.add_widget(btn_cancel)
        btn_row.add_widget(btn_save)
        root.add_widget(btn_row)

        self.content = root

    def _set_type(self, is_countup):
        self.btn_countdown.state = "normal" if is_countup else "down"
        self.btn_countup.state = "down" if is_countup else "normal"

    def _save(self):
        name = self.inp_name.text.strip()
        if not name:
            self.lbl_status.text = "⚠ Le nom est obligatoire."
            return
        if not self.chk_e.active and not self.chk_r.active:
            self.lbl_status.text = "⚠ Cochez au moins une option d'affichage."
            return
        try:
            dt = datetime.strptime(self.inp_date.text.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.lbl_status.text = "⚠ Format de date invalide (AAAA-MM-JJ HH:MM:SS)."
            return

        if not self.editing_event:
            for ex in self.config["events"]:
                if ex["name"].lower() == name.lower():
                    self.lbl_status.text = f"⚠ « {name} » existe déjà."
                    return

        new_ev = {
            "name": name,
            "date": dt.isoformat(),
            "type": "countup" if self.btn_countup.state == "down" else "countdown",
            "show_elapsed": self.chk_e.active,
            "show_remaining": self.chk_r.active,
        }

        if self.editing_event:
            for i, ev in enumerate(self.config["events"]):
                if ev["name"] == self.editing_event["name"]:
                    self.config["events"][i] = new_ev
                    break
        else:
            self.config["events"].append(new_ev)

        save_config(self.config)
        self.dismiss()
        if self.on_saved:
            self.on_saved(new_ev)


# ═══════════════════════════════════════════════════════════════════════════════
#  BOUTONS STYLISÉS (imports groupés en bas car dépendent du .kv chargé)
# ═══════════════════════════════════════════════════════════════════════════════
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton

class ButtonPink(Button):
    pass

class ButtonGhost(Button):
    pass

class ButtonMenu(Button):
    pass

class ButtonToggle(ToggleButton):
    pass


# ═══════════════════════════════════════════════════════════════════════════════
#  ÉCRANS
# ═══════════════════════════════════════════════════════════════════════════════
class MenuScreen(Screen):
    pass


class CompteursScreen(Screen):
    def on_pre_enter(self):
        self.reload()

    def reload(self):
        box = self.ids.cards_box
        for child in list(box.children):
            if hasattr(child, "stop"):
                child.stop()
        box.clear_widgets()
        app = App.get_running_app()
        events = app.config.get("events", [])
        if not events:
            box.add_widget(Label(text="Aucun compteur pour l'instant.\nAjoute ta première date ! 💖",
                                  color=C_PINK, font_name=FONT_NAME,
                                  size_hint_y=None, height=dp(80)))
            return
        for ev in events:
            card = EventCard(ev, on_edit=self._on_edit, on_delete=self._on_delete)
            box.add_widget(card)

    def _on_edit(self, event):
        app = App.get_running_app()
        popup = EventFormPopup(app.config, event=event, on_saved=lambda ev: self.reload())
        popup.open()

    def _on_delete(self, name):
        app = App.get_running_app()

        def _do_delete():
            app.config["events"] = [e for e in app.config["events"] if e["name"] != name]
            save_config(app.config)
            self.reload()
            dates_screen = self.manager.get_screen("dates")
            dates_screen.reload()

        confirm_popup("Confirmer", f"Supprimer « {name} » ?", _do_delete)


class AjouterScreen(Screen):
    def open_form(self):
        app = App.get_running_app()

        def _on_saved(ev):
            info_popup("Succès", f"✅ « {ev['name']} » enregistré !")
            compteurs = self.manager.get_screen("compteurs")
            compteurs.reload()
            dates = self.manager.get_screen("dates")
            dates.reload()

        popup = EventFormPopup(app.config, event=None, on_saved=_on_saved)
        popup.open()


class DatesScreen(Screen):
    def on_pre_enter(self):
        self.reload()

    def reload(self):
        box = self.ids.dates_box
        box.clear_widgets()
        app = App.get_running_app()
        events = app.config.get("events", [])
        if not events:
            box.add_widget(Label(text="Aucune date enregistrée pour l'instant.",
                                  color=C_PINK, font_name=FONT_NAME,
                                  size_hint_y=None, height=dp(60)))
            return
        for i, ev in enumerate(events):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                             spacing=dp(10), padding=(dp(12), dp(6)))
            row.add_widget(Label(text=f"#{i+1}", color=C_ROSE, font_name=FONT_NAME,
                                  size_hint_x=None, width=dp(36), bold=True))
            row.add_widget(Label(text=ev.get("name", ""), color=C_GOLD, font_name=FONT_NAME,
                                  bold=True, halign="left", valign="middle"))
            dt = parse_date(ev.get("date", ""))
            date_str = dt.strftime("%d/%m/%Y  %H:%M:%S") if dt else ev.get("date", "")
            row.add_widget(Label(text=date_str, color=C_TEXT, font_name=FONT_NAME))
            t = ev.get("type", "countdown")
            row.add_widget(Label(text=("⬇ countdown" if t == "countdown" else "⬆ countup"),
                                  color=C_PINK, font_name=FONT_NAME, size_hint_x=None, width=dp(110)))
            box.add_widget(row)


# ═══════════════════════════════════════════════════════════════════════════════
#  APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class CompteurApp(App):
    title = "Compteur Romantique 💖"
    font_name = FONT_NAME

    def build(self):
        self.icon = resource_path("icon.png") if os.path.exists(resource_path("icon.png")) else None
        Window.clearcolor = (0.05, 0.03, 0.09, 1)
        self.config = load_config()

        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()
        self.bg = ParticleBackground(size_hint=(1, 1))
        root.add_widget(self.bg)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.25), size_hint=(1, 1))
        self.sm.add_widget(MenuScreen(name="menu"))
        self.sm.add_widget(CompteursScreen(name="compteurs"))
        self.sm.add_widget(AjouterScreen(name="ajouter"))
        self.sm.add_widget(DatesScreen(name="dates"))
        root.add_widget(self.sm)

        Clock.schedule_once(lambda dt: self._start_music(), 1)
        return root

    def go(self, name):
        self.sm.current = name

    def quit_app(self):
        self.stop()

    def _start_music(self):
        if not os.path.exists(MUSIC_PATH):
            return
        try:
            self.sound = SoundLoader.load(MUSIC_PATH)
            if self.sound:
                self.sound.loop = True
                self.sound.volume = 0.3
                self.sound.play()
        except Exception as e:
            print(f"[music] {e}")


if __name__ == "__main__":
    CompteurApp().run()
