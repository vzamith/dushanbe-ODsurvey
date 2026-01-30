import os
import csv
from datetime import datetime

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.toast import toast
from kivy.metrics import dp
from kivy.utils import platform

# Import Plyer for Native Sharing features
try:
    from plyer import share
except ImportError:
    share = None

class SurveyApp(MDApp):
    # Variables to hold selections
    direction_value = ""
    origin_type_value = ""
    dest_type_value = ""
    mode_from_value = ""
    mode_to_value = ""
    frequency_value = ""
    
    valid_routes = [str(i) for i in range(1, 11)]

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # Storage setup
        if platform == 'android':
            from android.storage import app_storage_path
            self.data_dir = getattr(self, 'user_data_dir', '.')
        else:
            self.data_dir = os.getcwd()
        self.csv_file = os.path.join(self.data_dir, 'survey_data.csv')

        screen = MDScreen()
        scroll = MDScrollView()
        
        self.layout = MDBoxLayout(
            orientation='vertical', 
            padding=dp(10), 
            spacing=dp(15), 
            size_hint_y=None,
            md_bg_color=(0.96, 0.96, 0.96, 1) 
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # --- TITLE ---
        title_box = MDBoxLayout(size_hint_y=None, height=dp(50))
        title_box.add_widget(MDLabel(text="DUSHANBE's OD Survey", font_style="H5", halign="center", bold=True, theme_text_color="Custom", text_color=(0,0,0,1)))
        self.layout.add_widget(title_box)

        # --- BASIC INFO ---
        self.interviewer_id = self.add_row("Interviewer ID", self.create_white_field("Enter ID"))
        
        # Route Code
        self.route_field = self.add_dropdown_row("Route Code", self.valid_routes, editable=True)
        
        # --- DATE (Day / Month ONLY) ---
        # Returns a dict {'day': widget, 'month': widget}
        self.date_widgets = self.add_date_spinner_row("Date")

        # Direction
        self.add_tickbox_row("Direction", ["Inbound to City", "Outbound from City"], "direction_group")
        
        # --- TIME (Dropdown Selectors) ---
        # Returns a dict {'hour': widget, 'min': widget}
        self.start_time_widgets = self.add_time_spinner_row("Trip Start")
        self.end_time_widgets = self.add_time_spinner_row("Trip End")
        self.interview_time_widgets = self.add_time_spinner_row("Interview Time")

        self.add_divider()

        # --- SECTIONS ---
        self.origin = self.add_row("Origin", self.create_white_field("Street/Landmark"))
        self.add_tickbox_row("Origin Type", ["Home", "Work", "School", "Other"], "origin_group")

        self.dest = self.add_row("Destination", self.create_white_field("Street/Landmark"))
        self.add_tickbox_row("Dest Type", ["Home", "Work", "School", "Other"], "dest_group")

        self.add_divider()

        # --- TRANSFERS ---
        self.s2_yes = MDCheckbox(group="s2", size_hint=(None, None), size=(dp(48), dp(48)))
        self.s2_no = MDCheckbox(group="s2", active=True, size_hint=(None, None), size=(dp(48), dp(48))) 
        self.s2_yes.bind(active=self.toggle_section_2)
        self.add_yes_no_row("Transfer FROM another mode?", self.s2_yes, self.s2_no)

        modes = ["Bus", "Minibus", "Trolleybus", "Taxi"]
        self.mode_from_grid = self.add_tickbox_row("Mode (From)", modes, "mode_from_group")
        self.transfer_from_loc = self.add_row("Transfer Location", self.create_white_field("Street/Landmark"))
        
        self.set_grid_state(self.mode_from_grid, False)
        self.set_field_state(self.transfer_from_loc, False)

        self.add_divider()

        self.s3_yes = MDCheckbox(group="s3", size_hint=(None, None), size=(dp(48), dp(48)))
        self.s3_no = MDCheckbox(group="s3", active=True, size_hint=(None, None), size=(dp(48), dp(48)))
        self.s3_yes.bind(active=self.toggle_section_3)
        self.add_yes_no_row("Transfer TO another mode?", self.s3_yes, self.s3_no)

        self.mode_to_grid = self.add_tickbox_row("Mode (To)", modes, "mode_to_group")
        self.transfer_to_loc = self.add_row("Transfer Location", self.create_white_field("Street/Landmark"))

        self.set_grid_state(self.mode_to_grid, False)
        self.set_field_state(self.transfer_to_loc, False)

        self.add_divider()

        # --- FREQUENCY ---
        freq_options = ["Not a regular trip", "Once a week", "2-3 times a week", "5 times a week", "Everyday"]
        self.add_tickbox_row("Frequency", freq_options, "freq_group")

        # --- BUTTONS ---
        btn_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(120), padding=[0, 20, 0, 0])
        save_btn = MDRaisedButton(text="SAVE RECORD", size_hint=(1, None), height=dp(50), on_release=self.save_data)
        export_btn = MDFlatButton(text="EXPORT / SHARE CSV", size_hint=(1, None), height=dp(50), on_release=self.export_data)
        
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(export_btn)
        self.layout.add_widget(btn_layout)

        scroll.add_widget(self.layout)
        screen.add_widget(scroll)
        return screen

    # --- UI HELPERS ---
    def create_white_field(self, hint, readonly=False, error_check=False):
        field = MDTextField(
            hint_text=hint, 
            readonly=readonly, 
            mode="fill", 
            fill_color_normal=(1, 1, 1, 1),
            fill_color_focus=(1, 1, 1, 1)
        )
        if error_check:
            field.helper_text_mode = "on_error"
            field.helper_text = "Invalid Option"
            field.error_color = (1, 0, 0, 1)
        return field

    def add_row(self, label_text, widget):
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(10))
        lbl = MDLabel(text=label_text, size_hint_x=0.35, valign='center', bold=True, theme_text_color="Custom", text_color=(0, 0, 0, 1))
        widget.size_hint_x = 0.65
        row.add_widget(lbl)
        row.add_widget(widget)
        self.layout.add_widget(row)
        return widget

    # --- CUSTOM SPINNER HELPERS ---
    def create_spinner(self, items, hint_text, width_hint=1):
        """Creates a small dropdown field that looks like a spinner"""
        field = self.create_white_field(hint_text, readonly=True)
        menu_items = [{"viewclass": "OneLineListItem", "text": str(i), "on_release": lambda x=str(i): self.set_item(field, x)} for i in items]
        field.menu = MDDropdownMenu(caller=field, items=menu_items, width_mult=2, max_height=dp(250))
        field.bind(on_focus=lambda instance, x: field.menu.open() if x else None)
        field.size_hint_x = width_hint
        return field

    def add_time_spinner_row(self, label_text):
        """Adds [Hour] [Minute] dropdowns"""
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(5))
        lbl = MDLabel(text=label_text, size_hint_x=0.35, valign='center', bold=True, theme_text_color="Custom", text_color=(0, 0, 0, 1))
        
        # Hours: 00 to 23
        hours = [f"{i:02d}" for i in range(24)]
        hour_field = self.create_spinner(hours, "HH")
        
        # Separator :
        sep = MDLabel(text=":", size_hint_x=None, width=dp(10), halign="center", bold=True)

        # Minutes: 00 to 59
        minutes = [f"{i:02d}" for i in range(60)]
        min_field = self.create_spinner(minutes, "MM")
        
        row.add_widget(lbl)
        row.add_widget(hour_field)
        row.add_widget(sep)
        row.add_widget(min_field)
        self.layout.add_widget(row)
        
        return {'hour': hour_field, 'min': min_field}

    def add_date_spinner_row(self, label_text):
        """Adds [Day] [Month] dropdowns ONLY"""
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(5))
        lbl = MDLabel(text=label_text, size_hint_x=0.35, valign='center', bold=True, theme_text_color="Custom", text_color=(0, 0, 0, 1))
        
        # Day: 01-31
        days = [f"{i:02d}" for i in range(1, 32)]
        day_field = self.create_spinner(days, "Day", width_hint=0.45) # Slightly wider now
        
        # Month: Jan-Dec
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_field = self.create_spinner(months, "Month", width_hint=0.55) # Slightly wider now
        
        # No Year Field Added
        
        row.add_widget(lbl)
        row.add_widget(day_field)
        row.add_widget(month_field)
        self.layout.add_widget(row)
        
        return {'day': day_field, 'month': month_field}

    # --- STANDARD HELPERS ---
    def add_dropdown_row(self, label_text, items, editable=False):
        field = self.create_white_field("Select or Type...", readonly=not editable, error_check=editable)
        menu_items = [{"viewclass": "OneLineListItem", "text": i, "on_release": lambda x=i: self.set_item(field, x)} for i in items]
        field.menu = MDDropdownMenu(caller=field, items=menu_items, width_mult=4, max_height=dp(200))
        
        if editable:
            field.bind(focus=lambda instance, has_focus: self.validate_dropdown(instance, has_focus, items))
            field.bind(on_focus=lambda instance, x: field.menu.open() if x else None)
        else:
            field.bind(on_focus=lambda instance, x: field.menu.open() if x else None)

        return self.add_row(label_text, field)

    def validate_dropdown(self, field, has_focus, items):
        if not has_focus:
            if field.text and field.text not in items:
                field.error = True
            else:
                field.error = False
        else:
            field.menu.open()

    def add_tickbox_row(self, label_text, options, group_name):
        lbl = MDLabel(text=label_text, size_hint_y=None, height=dp(30), bold=True, theme_text_color="Custom", text_color=(0,0,0,1))
        self.layout.add_widget(lbl)
        grid = MDGridLayout(
            cols=2, adaptive_height=True, padding=dp(10), spacing=dp(5),
            md_bg_color=(1, 1, 1, 1), radius=[6, 6, 6, 6]
        )
        for opt in options:
            item_box = MDBoxLayout(orientation='horizontal', size_hint_x=1, spacing=dp(5), adaptive_height=True)
            chk = MDCheckbox(group=group_name, size_hint=(None, None), size=(dp(30), dp(30)))
            chk.bind(active=lambda instance, val, txt=opt, grp=group_name: self.on_checkbox_active(val, txt, grp))
            lbl_opt = MDLabel(text=opt, theme_text_color="Primary", font_style="Caption", valign='center')
            item_box.add_widget(chk)
            item_box.add_widget(lbl_opt)
            grid.add_widget(item_box)
        self.layout.add_widget(grid)
        return grid

    def add_yes_no_row(self, question_text, yes_chk, no_chk):
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        lbl = MDLabel(text=question_text, size_hint_x=0.6, bold=True, theme_text_color="Custom", text_color=(0,0,0,1), valign='center')
        yes_box = MDBoxLayout(orientation='horizontal', size_hint_x=0.2)
        yes_box.add_widget(yes_chk)
        yes_box.add_widget(MDLabel(text="Yes"))
        no_box = MDBoxLayout(orientation='horizontal', size_hint_x=0.2)
        no_box.add_widget(no_chk)
        no_box.add_widget(MDLabel(text="No"))
        row.add_widget(lbl)
        row.add_widget(yes_box)
        row.add_widget(no_box)
        self.layout.add_widget(row)

    def add_divider(self):
        self.layout.add_widget(MDBoxLayout(size_hint_y=None, height=dp(15)))
        
    def set_item(self, field, text_item):
        field.text = text_item
        field.error = False
        field.menu.dismiss()
    
    def set_field_state(self, field, enabled):
        field.disabled = not enabled
        field.opacity = 1.0 if enabled else 0.5

    def set_grid_state(self, grid, enabled):
        grid.disabled = not enabled
        grid.opacity = 1.0 if enabled else 0.5

    def on_checkbox_active(self, is_active, text, group):
        if not is_active: return
        if group == "direction_group": self.direction_value = text
        elif group == "origin_group": self.origin_type_value = text
        elif group == "dest_group": self.dest_type_value = text
        elif group == "mode_from_group": self.mode_from_value = text
        elif group == "mode_to_group": self.mode_to_value = text
        elif group == "freq_group": self.frequency_value = text

    def toggle_section_2(self, instance, value):
        self.set_grid_state(self.mode_from_grid, value)
        self.set_field_state(self.transfer_from_loc, value)
        if not value:
            self.transfer_from_loc.text = ""
            self.mode_from_value = "" 

    def toggle_section_3(self, instance, value):
        self.set_grid_state(self.mode_to_grid, value)
        self.set_field_state(self.transfer_to_loc, value)
        if not value:
            self.transfer_to_loc.text = ""
            self.mode_to_value = ""

    def save_data(self, instance):
        if self.route_field.error:
            toast("Please correct the Route Code.")
            return

        # Combine Date parts (Append Current Year automatically)
        d = self.date_widgets
        current_year = datetime.now().year
        date_str = f"{d['day'].text}-{d['month'].text}-{current_year}"
        
        # Combine Time parts
        def get_time(widgets):
            return f"{widgets['hour'].text}:{widgets['min'].text}"

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.interviewer_id.text,
            self.route_field.text,
            date_str, 
            self.direction_value, 
            get_time(self.start_time_widgets),
            get_time(self.end_time_widgets),
            get_time(self.interview_time_widgets),
            self.origin.text,
            self.origin_type_value, 
            self.dest.text,
            self.dest_type_value,
            "Yes" if self.s2_yes.active else "No",
            self.mode_from_value if self.s2_yes.active else "",
            self.transfer_from_loc.text,
            "Yes" if self.s3_yes.active else "No",
            self.mode_to_value if self.s3_yes.active else "",
            self.transfer_to_loc.text,
            self.frequency_value
        ]
        
        headers = ["Timestamp", "ID", "Route", "Date", "Direction", "Start", "End", "Interview Time", 
                   "Origin", "Origin Type", "Dest", "Dest Type", 
                   "Transfer From?", "Mode From", "Loc From", 
                   "Transfer To?", "Mode To", "Loc To", "Frequency"]
        
        try:
            file_exists = os.path.isfile(self.csv_file)
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';') 
                if not file_exists:
                    writer.writerow(headers)
                writer.writerow(row)
            toast("Record Saved!")
        except Exception as e:
            toast(f"Error: {e}")

    def export_data(self, instance):
        if not os.path.isfile(self.csv_file):
            toast("No data file found.")
            return
        if share:
            share.file_share(file_path=self.csv_file)
        else:
            toast(f"File at: {self.csv_file}")

if __name__ == '__main__':
    SurveyApp().run()