from datetime import datetime

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (
    Color,
    Ellipse,
    RoundedRectangle,
    StencilPop,
    StencilPush,
    StencilUnUse,
    StencilUse,
)
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen, ScreenManager, WipeTransition
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.toast.kivytoast.kivytoast import toast
from kivymd.uix.behaviors import RectangularElevationBehavior, RectangularRippleBehavior
from kivymd.uix.list import MDList
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.taptargetview import MDTapTargetView

from scripts.core import PlantifyCore
from widgets.debugdialog import DebugDialog

if platform == "android":
    from scripts.camera_jvinicius import CameraAndroid


class Manager(ScreenManager):
    pass


class MainScreen(Screen):
    camera_button = ObjectProperty()

    debugging = True

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        if platform == "android":
            Clock.schedule_once(self.runtime_permissions, 0.5)
        Clock.schedule_once(self.deferred, 1)

    def deferred(self, *args):
        self.button_taptarget = MDTapTargetView(
            widget=self.camera_button,
            title_text="Welcome to Plantify!",
            description_text="Tap the camera button to start!",
            widget_position="top",
            target_circle_color=MDApp.get_running_app().theme_cls.primary_dark[:-1],
            cancelable=True,
        )

        self.button_taptarget.start()

        Clock.schedule_once(lambda *args: self.button_taptarget.stop(), 5)

    def runtime_permissions(self, *args):
        from android.permissions import Permission, request_permissions

        request_permissions(
            [
                Permission.CAMERA,
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]
        )

    def camera_prompt(self):
        now = datetime.now()
        self.image_name = "PTFY_{}_{}_".format(
            "".join([str(i) for i in (now.year, now.month, now.day)]),
            "".join([str(i) for i in (now.hour, now.minute, now.second)]),
        )

        if platform == "android":
            CameraAndroid(self.image_name).take_picture(
                on_complete=lambda *args: Clock.schedule_once(
                    lambda *args_: self.camera_callback(*args), 3
                )
            )

        else:
            if not self.debugging:
                toast("Sorry, your platform is not supported!")
            else:
                Snackbar(text="This should open the camera. . .").show()
                self.camera_callback("samples/plant-image.jpg")

    def camera_callback(self, filepath):
        self.manager.transition = WipeTransition()
        self.manager.current = "sub"
        self.manager.get_screen("sub").take_control(filepath)

    def show_debug(self):
        DebugDialog("This is a debug", "warning").open()


class SubScreen(Screen):
    api = PlantifyCore()

    container_list = ObjectProperty()
    captured_image = ObjectProperty()
    backdrop = ObjectProperty()
    loader = ObjectProperty()
    backdrop_button = ObjectProperty()

    network_test = False

    taptarget_shown = False

    ##    def __init__(self, **kwargs):
    ##        super(SubScreen, self).__init__(**kwargs)
    ##
    ##        Clock.schedule_once(self.deferred, 1)

    def deferred(self, *args):
        self.backdrop_taptarget = MDTapTargetView(
            widget=self.backdrop_button,
            title_text="Results will be displayed in this screen",
            description_text="Tap here to view your capture and for \nadditional options!",
            widget_position="left_top",
            outer_circle_alpha=1,
            target_circle_color=MDApp.get_running_app().theme_cls.accent_dark[:-1],
            cancelable=True,
        )

        self.backdrop_taptarget.start()

    def take_control(self, image_path):
        if not self.taptarget_shown:
            self.deferred()
            self.taptarget_shown = True

        self.captured_image.source = image_path

        self.captured_image.width = Window.width
        self.captured_image.height = self.captured_image.texture_size[1] * (
            self.captured_image.width / self.captured_image.texture_size[0]
        )

        height_threshold = Window.height * (11 / 26)

        self.captured_image.y = Window.height - self.captured_image.height + 30
        if self.captured_image.height > height_threshold:
            self.captured_image.y += self.captured_image.height - height_threshold

        self.send_request()

    def send_request(self):
        self.loader.active = True

        should_send_request = True
        if platform == "android":
            will_debug = False
        else:
            if self.network_test:
                will_debug = True
            else:
                should_send_request = False

        if should_send_request:
            delay = 1
            self.api.get_response_for(
                image=self.captured_image.source,
                debugging=will_debug,
                func_success=lambda *args: Clock.schedule_once(
                    lambda *args_: self.if_success(*args), delay
                ),
                func_failure=lambda *args: Clock.schedule_once(
                    lambda *args_: self.if_failure(*args), delay
                ),
                func_error=lambda *args: Clock.schedule_once(
                    lambda *args_: self.if_error(*args), delay
                ),
                func_progress=self.if_progress,
            )
        else:
            Clock.schedule_once(self.if_success, 1)

    def if_success(self, *args):
        toast("Success! Showing results. . .")

        self.loader.active = False
        if self.backdrop._front_layer_open:
            self.backdrop.close()

        # args = [instance, results]
        # Assuming a good response was returned, args[1]['results'] will have the result JSON

        try:
            if platform == "android" or self.network_test:
                api_results = args[1]["results"]
                remaining = args[1]["remainingIdentificationRequests"]
            else:
                api_results = self.api.SAMPLE_RESPONSE["results"]
                remaining = self.api.SAMPLE_RESPONSE["remainingIdentificationRequests"]

            score = remaining / 50
            test = [
                ((-116 * score) + 255),
                ((113 * score) + 82),
                ((-8 * score) + 82),
            ]

            hex_ = "#{:02X}{:02X}{:02X}".format(*[int(i // 1) for i in test])

            self.backdrop.header_text = (
                f"Remaining requests: [color={hex_}]{remaining}[/color]"
            )

            self.container_list.generate_cards(api_results)
        except Exception as e:
            toast(str(repr(e)))

    def if_failure(self, *args):
        print("Fail :( >>", args)
        toast("Something has failed.")

        self.loader.active = False

    def if_error(self, *args):
        print("ERROR:", args)
        toast("An error has occurred.")

        self.loader.active = False

    def if_progress(self, *args):
        print("On progress. . .")

    def change_plant_type(self, type_):
        self.api.organ = type_
        self.reset_list()
        self.send_request()

        Snackbar(
            text=f'Organ type set to "{self.api.organ}"\nThis probably does not work lol'
        ).show()

    def reset_list(self, *args):
        self.container_list.clear_widgets()
        self.backdrop.header_text = "Waiting for response. . ."

        if self.backdrop._front_layer_open:
            self.backdrop.close()


class SubList(MDList):
    def generate_cards(self, results):
        self.cards = []

        for index, item in enumerate(results):
            score = item["score"]

            species = item["species"]
            scientific_name = species["scientificNameWithoutAuthor"]
            genus = species["genus"]["scientificNameWithoutAuthor"]
            family = species["family"]["scientificNameWithoutAuthor"]

            common_name_results = species["commonNames"]
            common_names = (
                scientific_name
                if common_name_results == []
                else (
                    ", ".join(common_name_results[:-1])
                    + f", or {common_name_results[-1]}"
                    if len(common_name_results) > 1
                    else common_name_results[0]
                )
            )
            common_names = common_names.replace("-", " — ")

            card = SubCardListItem()

            if common_names == scientific_name:
                scientific_name = ""
                card.ids.common.italic = True

            if len(common_names) > 55:
                card.ids.common.font_size = "16sp"  # noqa: E701

            card.ids["match"].text = f"Match: {score * 100:.2f}%"
            card.ids["common"].text = common_names
            card.ids["scientific"].text = scientific_name
            card.ids["flavor"].text = f"Genus {genus}, of family {family}."

            card.ids["match"].text_color = [
                ((-116 * score) + 255) / 255,
                ((113 * score) + 82) / 255,
                ((-8 * score) + 82) / 255,
                1,
            ]

            if index == 0 and score > 0.0:
                card.ids["sep"].color = card.ids["match"].text_color

            self.add_widget(card)
            self.cards.append(card)


class CustomRoundedRectangularRippleBehavior(RectangularRippleBehavior):
    def lay_canvas_instructions(self):
        if self._no_ripple_effect:
            return
        with self.canvas.after:
            StencilPush()
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.rad)
            StencilUse()
            self.col_instruction = Color(rgba=self.ripple_color)
            self.ellipse = Ellipse(
                size=(self._ripple_rad, self._ripple_rad),
                pos=(
                    self.ripple_pos[0] - self._ripple_rad / 2.0,
                    self.ripple_pos[1] - self._ripple_rad / 2.0,
                ),
            )
            StencilUnUse()
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.rad)
            StencilPop()
        self.bind(ripple_color=self._set_color, _ripple_rad=self._set_ellipse)


class SubCardListItem(
    ThemableBehavior,
    CustomRoundedRectangularRippleBehavior,
    RectangularElevationBehavior,
    ButtonBehavior,
    FloatLayout,
):
    r_value = 12
    rad = (lambda rv: [rv for i in range(4)])(r_value)

    def toast_bridge(self):
        match = self.ids["match"]
        scientific = self.ids["scientific"]
        common = self.ids["common"]
        message = f'[{match.text.lower().capitalize()}] {scientific.text if scientific.text != "" else common.text}'

        # toast(message)
        Snackbar(text=message).show()


class PlantifyMD(MDApp):
    def __init__(self, **kwargs):
        super(PlantifyMD, self).__init__(**kwargs)

        self.title = "PlantifyMD"
        # self.theme_cls.theme_style = 'Dark'

        self.theme_cls.primary_palette = "LightGreen"
        # self.theme_cls.primary_hue = 'A100'

        self.theme_cls.accent_palette = "Amber"
        # self.theme_cls.accent_hue = 'A100'

        """ Possible palettes
            'Red', 'Pink', 'Purple', 'DeepPurple', 'Indigo', 'Blue', 'LightBlue',
            'Cyan', 'Teal', 'Green', 'LightGreen', 'Lime', 'Yellow', 'Amber',
            'Orange', 'DeepOrange', 'Brown', 'Gray', 'BlueGray' """

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == "__main__":
    instance = PlantifyMD()

    if platform != "android":
        Window.size = (400, 600)  # noqa: E701
    # if platform != 'android': Window.size = (325, 650)  # 18:9  # noqa: E701
    # if platform != 'android': Window.size = (366, 650)    # 16:9  # noqa: E701

    platform = "[DEBUGGING]"

    instance.run()
