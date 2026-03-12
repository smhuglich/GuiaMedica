import asyncio
import os
import webbrowser
from collections import defaultdict

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.fitimage import FitImage
from kivy.metrics import dp
from kivy.utils import platform
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.logger import Logger
import logging

# --- Configuración de Logs ---
def setup_logging():
    try:
        if platform == 'android':
            from android.storage import app_storage_path
            log_dir = os.path.join(app_storage_path(), 'logs')
        else:
            log_dir = os.path.dirname(os.path.abspath(__file__))

        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app_log.txt")
        
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger('kivy').addHandler(fh)
        
        Logger.info(f"Logging initialized. File: {log_file}")
        return log_file
    except Exception as e:
        Logger.error(f"Failed to initialize file logging: {e}")
        return None

try:
    import httpx
except ImportError:
    httpx = None

# URL de la API (Provisional)
API_BASE_URL = "https://medical-app-api.onrender.com" # Cambiar por la URL real cuando esté deployed

# --------------------------------------------------
# DATABASE (API Access)
# --------------------------------------------------

class DatabaseManager:
    def __init__(self):
        self.base_url = API_BASE_URL
        Logger.info(f"DatabaseManager: Using API at {self.base_url}")

    async def get_specialties(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/specialties", timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            Logger.error(f"API Error (get_specialties): {e}")
            raise e

    async def get_institutions_by_specialty(self, specialty_id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/institutions/{specialty_id}", timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            Logger.error(f"API Error (get_institutions): {e}")
            raise e

    # --- ABM Methods ---

    async def add_institution(self, nombre, direccion, telefono, lat=None, lng=None):
        try:
            async with httpx.AsyncClient() as client:
                data = {"nombre": nombre, "direccion": direccion, "telefono": telefono, "lat": lat, "lng": lng}
                response = await client.post(f"{self.base_url}/institutions", json=data, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise e

    async def update_institution(self, id, nombre, direccion, telefono, lat, lng):
        try:
            async with httpx.AsyncClient() as client:
                data = {"nombre": nombre, "direccion": direccion, "telefono": telefono, "lat": lat, "lng": lng}
                response = await client.put(f"{self.base_url}/institutions/{id}", json=data, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            Logger.error(f"API Error (update_institution): {e}")
            raise e

    async def delete_institution(self, id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.base_url}/institutions/{id}", timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            Logger.error(f"API Error (delete_institution): {e}")
            raise e

    # NOTE: The other ABM methods (professionals, specialties, schedules) 
    # should be implemented similarly if needed by this app.
    # For now, focus on the ones used by the main UI.

def create_db_manager():
    """Factory: returns the DatabaseManager."""
    if httpx is None:
        raise ImportError("httpx not found. Please install it.")
    return DatabaseManager()

# --------------------------------------------------
# UI CARD
# --------------------------------------------------

class InstitutionCard(MDBoxLayout):
    def __init__(self, inst, schedules, call_cb, map_cb, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(0.05, 0.2, 0.4, 1)
            self.line = Line(points=[0, 0, 0, 0], width=1)
        self.bind(size=self.update_line, pos=self.update_line)

        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), padding=dp(10))
        text = MDBoxLayout(orientation="vertical")
        text.add_widget(MDLabel(text=inst["nombre"], font_style="Subtitle1", theme_text_color="Primary"))
        text.add_widget(MDLabel(text=inst["direccion"], font_style="Caption", theme_text_color="Secondary"))
        row.add_widget(text)

        actions = MDBoxLayout(orientation="horizontal", size_hint_x=None, width=dp(100), spacing=dp(5))
        if inst["telefono"]:
            btn = MDIconButton(icon="phone", theme_text_color="Custom", text_color=[0.05, 0.2, 0.4, 1])
            btn.bind(on_release=lambda x: call_cb(inst["telefono"]))
            actions.add_widget(btn)

        btn_map = MDIconButton(icon="map-marker-radius", theme_text_color="Custom", text_color=[0.05, 0.2, 0.4, 1])
        btn_map.bind(on_release=lambda x: map_cb(inst))
        actions.add_widget(btn_map)
        row.add_widget(actions)
        self.add_widget(row)

        if schedules:
            sched_box = MDBoxLayout(orientation="vertical", size_hint_y=None, padding=[dp(16), 0, dp(16), dp(10)])
            sched_box.bind(minimum_height=sched_box.setter("height"))
            
            day_map = {1: "LU", 2: "MA", 3: "MI", 4: "JU", 5: "VI", 6: "SA", 7: "DO"}
            profs = defaultdict(list)
            for s in schedules:
                profs[s["prof"]].append(s)

            for p, rows in profs.items():
                box = MDBoxLayout(
                    orientation="vertical", size_hint_y=None, 
                    md_bg_color=[0.74, 0.78, 0.55, 1], padding=[dp(8), dp(4), dp(8), dp(4)],
                    radius=[dp(4)], spacing=dp(2)
                )
                box.bind(minimum_height=box.setter("height"))
                box.add_widget(MDLabel(text=f"[b]{p.upper()}[/b]", markup=True, size_hint_y=None, height=dp(25), font_style="Caption"))

                for r in rows:
                    line = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(18))
                    day_name = day_map.get(r['dia_num'], str(r['dia_num']))
                    line.add_widget(MDLabel(text=day_name, font_style="Caption", theme_text_color="Secondary"))
                    line.add_widget(MDLabel(text=f"{r['inicio']}-{r['fin']}", halign="right", font_style="Caption", theme_text_color="Secondary"))
                    box.add_widget(line)
                
                sched_box.add_widget(box)
                sched_box.add_widget(MDBoxLayout(size_hint_y=None, height=dp(5)))
            self.add_widget(sched_box)

    def update_line(self, *a):
        self.line.points = [self.x, self.y, self.x + self.width, self.y]

# --------------------------------------------------
# SCREEN
# --------------------------------------------------

class MainScreen(Screen):
    pass

# --------------------------------------------------
# APP
# --------------------------------------------------

class MedicalApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.spec_map = {}

    def build(self):
        try:
            self.theme_cls.primary_palette = "Blue"
            Logger.info("App: Initializing DatabaseManager...")
            self.db = create_db_manager()
            Logger.info("App: DatabaseManager initialized successfully")

            self.sm = ScreenManager()
            screen = MainScreen(name="main")
            layout = MDBoxLayout(orientation="vertical")
            
            app_bar = MDTopAppBar(title="Guia Medica")
            layout.add_widget(app_bar)

            filter_area = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=10, spacing=5)
            self.spec_field = MDTextField(hint_text="1. Elija Especialidad", readonly=True)
            self.spec_field.bind(on_touch_down=self.open_menu)
            filter_area.add_widget(self.spec_field)
            layout.add_widget(filter_area)

            self.prog = MDProgressBar(type="indeterminate", opacity=0, size_hint_y=None, height=dp(4))
            layout.add_widget(self.prog)

            self.scroll = MDScrollView(bar_width=dp(4), scroll_type=['bars', 'content'], effect_cls="DampedScrollEffect")
            self.list_ui = MDList()
            self.scroll.add_widget(self.list_ui)
            layout.add_widget(self.scroll)

            # Footer
            footer = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70), padding=[dp(20), dp(5), dp(20), dp(5)], spacing=dp(10), md_bg_color=[1, 1, 1, 1])
            logo_img = "studio_logo.png"
            if os.path.exists(logo_img):
                logo = FitImage(source=logo_img, size_hint=(None, None), size=(dp(40), dp(40)), radius=[dp(20)], pos_hint={'center_y': 0.5})
            else:
                logo = MDLabel(text="LOGO", size_hint=(None, None), size=(dp(40), dp(40)))
            
            info_box = MDBoxLayout(orientation='vertical', spacing=dp(2), pos_hint={'center_y': 0.5})
            info_box.add_widget(MDLabel(text="STUDIO SOFTWARE", font_style="Subtitle2", theme_text_color="Primary"))
            info_box.add_widget(MDLabel(text="sergiohuglich1@gmail.com", font_style="Caption", theme_text_color="Secondary"))
            
            footer.add_widget(logo)
            footer.add_widget(info_box)
            layout.add_widget(footer)

            screen.add_widget(layout)
            self.sm.add_widget(screen)
            self.menu = None
            Window.bind(on_keyboard=self.on_key_down)
            return self.sm
        except Exception as e:
            Logger.error(f"CRITICAL BUILD ERROR: {e}")
            return MDLabel(text=f"Error al iniciar:\n{str(e)}", halign="center")

    def on_start(self):
        if self.db:
            asyncio.create_task(self.load_specs())
        else:
            Logger.error("App: Skipping load_specs because db is not initialized")

    def on_key_down(self, window, key, *args):
        if key == 27:
            if self.menu and self.menu.parent:
                self.menu.dismiss()
                return True
            if self.list_ui.children:
                self.list_ui.clear_widgets()
                self.spec_field.text = ""
                return True
        return False

    async def load_specs(self):
        if not self.db:
            self.show_error_dialog("Error", "Base de datos no inicializada.")
            return

        try:
            specs = await self.db.get_specialties()
            self.spec_map = {s["nombre"]: s["id"] for s in specs}
            items = [{"text": s["nombre"], "viewclass": "OneLineListItem", "on_release": lambda x=s["nombre"]: self.set_spec(x)} for s in specs]
            self.menu = MDDropdownMenu(caller=self.spec_field, items=items, width_mult=4)
        except Exception as e:
            self.show_error_dialog("Error", f"No se pudo conectar a la base de datos:\n{e}")

    def show_error_dialog(self, title, text):
        dialog = MDDialog(
            title=title, text=text,
            buttons=[MDFlatButton(text="CERRAR", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def open_menu(self, inst, touch):
        if inst.collide_point(*touch.pos) and self.menu:
            self.menu.open()

    def set_spec(self, name):
        self.spec_field.text = name
        self.menu.dismiss()
        asyncio.create_task(self.fetch_data(name))

    async def fetch_data(self, spec_name):
        if not self.db:
            self.show_error_dialog("Error", "Base de datos no inicializada.")
            return

        self.prog.opacity = 1
        self.prog.start()
        sid = self.spec_map[spec_name]
        try:
            data = await self.db.get_institutions_by_specialty(sid)
            self.update_list(data)
        except Exception as e:
            self.show_error_dialog("Error", "No se pudieron obtener los datos.")
        self.prog.stop()
        self.prog.opacity = 0

    def update_list(self, data):
        self.list_ui.clear_widgets()
        for item in data:
            card = InstitutionCard(item["info"], item["scheds"], self.call_phone, self.open_map)
            self.list_ui.add_widget(card)

    def call_phone(self, num):
        webbrowser.open(f"tel:{num}")

    def open_map(self, inst):
        if inst.get("lat") and inst.get("lng"):
            url = f"https://www.google.com/maps/search/?api=1&query={inst['lat']},{inst['lng']}"
        else:
            query = f"{inst['direccion']}, San Rafael, Mendoza".replace(" ", "+")
            url = f"https://www.google.com/maps/search/?api=1&query={query}"
        webbrowser.open(url)

if __name__ == "__main__":
    setup_logging()
    app = MedicalApp()
    try:
        asyncio.run(app.async_run(async_lib="asyncio"))
    except Exception as e:
        Logger.error(f"FATAL ERROR: {e}")
        raise e