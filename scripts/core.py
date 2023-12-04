import imghdr
import io
import urllib.parse

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, RoundedRectangle
from kivy.network.urlrequest import UrlRequest
from PIL import Image
from requests_toolbelt import MultipartEncoder


class PlantifyCore:
    SERVICE_URL = "https://my-api.plantnet.org/v2/identify/all"
    API = "API_KEY_HERE"  # TODO Initialize API key

    SAMPLE_RESPONSE = ""
    with open("samples/api-output.txt", "r") as f:
        SAMPLE_RESPONSE = eval(f.read())  # noqa: E701
    # with open('samples/api-output.txt', 'r') as f: SAMPLE_RESPONSE = eval(f.read())   # noqa: E701

    organ = "flower"

    def get_response_for(
        self,
        image,
        debugging,
        func_success=None,
        func_failure=None,
        func_error=None,
        func_progress=None,
    ):
        url = f"{self.SERVICE_URL}?api-key={self.API}"
        # url = 'https://httpbin.org/post'

        if not debugging:
            processing = Image.open(image)
            processed = processing.resize(
                [i // 2 for i in processing.size], resample=Image.ANTIALIAS
            )

            buffer = io.BytesIO()
            processed.save(buffer, "JPEG")

            images = (image.split("_")[-1], buffer.getvalue())
        else:
            images = (image[image.index("/") + 1 :], open(image, "rb"))

        mp = MultipartEncoder(
            fields={
                "organs": self.organ,
                "images": images,
            }
        )

        UrlRequest(
            url,
            on_success=func_success,  # lambda *args: print(f'Success: {args}'),
            on_failure=func_failure,  # lambda *args: print(f'Failure: {args}'),
            on_error=func_error,  # lambda *args: print(f'Error: {args}'),
            on_progress=func_progress,  # lambda *args: print(f'Progress: {args}'),
            req_body=mp,
            req_headers={"Content-Type": mp.content_type},
            verify=False,
        )


class ImageQuery:
    BASE_URL = "https://www.googleapis.com/customsearch/v1?"
    API = "API_KEY_HERE"  # TODO Initialize API key
    CSE_ID = "CSE_ID_HERE"  # TODO Initialize CSE ID

    def __init__(self, widget):
        self.widget = widget

    def get_image_for(self, query):
        parameters = {
            "key": self.API,
            "cx": self.CSE_ID,
            "q": query,
            "searchType": "image",
        }

        url_affix = urllib.parse.urlencode(parameters)

        UrlRequest(
            self.BASE_URL + url_affix,
            on_success=self.success,
            on_failure=self.failure,
            on_error=self.error,
            verify=False,
        )

    def success(self, *args):
        json = args[1]

        items = json["items"]
        links = [item["link"] for item in items[:3]]

        self.image_dict = {
            1: self.widget.image_1,
            2: self.widget.image_2,
            3: self.widget.image_3,
        }

        self.counter = 1
        for link in links:
            UrlRequest(
                link,
                on_success=self.new_image,
                verify=False,
            )

    def failure(self, *args):
        print("Fail!", args)

    def error(self, *args):
        print("Err!", args)

    def new_image(self, *args):
        image_type = imghdr.what(None, h=args[1])

        img = Image.open(io.BytesIO(args[1]))
        resized = img.resize([80, 80], resample=Image.ANTIALIAS)

        buffer = io.BytesIO()
        resized.save(buffer, image_type)

        buffer.seek(0)

        c_image = CoreImage(io.BytesIO(buffer.read()), ext=image_type)

        # self.image_dict[self.counter].texture = c_image.texture
        with self.image_dict[self.counter].canvas:
            Color(rgba=[1, 1, 1, 1])
            RoundedRectangle(
                pos=self.image_dict[self.counter].pos,
                size=self.image_dict[self.counter].size,
                texture=c_image.texture,
            )

        self.counter += 1
