from kivymd.uix.dialog import MDDialog


class DebugDialog(MDDialog):
    def __init__(self, text, title_type, **kwargs):
        title_dict = {'good':'Nice!',
                      'warning': 'Attention!',
                      'bad': 'Uh-oh!'}

        self.title = title_dict[title_type]
        self.text = text

        super(DebugDialog, self).__init__(**kwargs)