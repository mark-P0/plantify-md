from kivymd.uix.dialog import MDDialog

TITLES = {
    "good": "Nice!",
    "warning": "Attention!",
    "bad": "Uh-oh!",
}


class DebugDialog(MDDialog):
    def __init__(self, text, title_type, **kwargs):
        self.title = TITLES[title_type]
        self.text = text

        super(DebugDialog, self).__init__(**kwargs)
