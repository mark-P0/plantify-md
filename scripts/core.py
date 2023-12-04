import imghdr
import io
from urllib.parse import urlencode

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, RoundedRectangle
from kivy.network.urlrequest import UrlRequest
from PIL import Image
from requests_toolbelt import MultipartEncoder


def create_url(base: str, *paths: str, **queries: str) -> str:
    """
    https://stackoverflow.com/a/43934565

    TODO Opt for a more robust approach? i.e. not string concatenations...
    """

    url = "/".join(part.strip("/") for part in (base, *paths))

    if len(queries) > 0:
        url += "?" + urlencode(queries)

    return url


API_URL = create_url(
    "https://my-api.plantnet.org/v2/identify/all",
    **{"api-key": "API_KEY_HERE"},  # TODO Initialize API key
)


class PlantifyCore:
    SAMPLE_RESPONSE = ""
    with open("samples/api-output.txt", "r") as f:
        SAMPLE_RESPONSE = eval(f.read())

    organ = "flower"

    def get_images(self, image, debugging):
        if debugging:
            return (image[image.index("/") + 1 :], open(image, "rb"))

        processing = Image.open(image)
        processed = processing.resize(
            [i // 2 for i in processing.size], resample=Image.ANTIALIAS
        )

        buffer = io.BytesIO()
        processed.save(buffer, "JPEG")

        return (image.split("_")[-1], buffer.getvalue())

    def get_response_for(
        self,
        image,
        debugging,
        func_success=None,
        func_failure=None,
        func_error=None,
        func_progress=None,
    ):
        images = self.get_images(image, debugging)

        mp = MultipartEncoder(
            fields={
                "organs": self.organ,
                "images": images,
            }
        )
        UrlRequest(
            API_URL,
            on_success=func_success,
            on_failure=func_failure,
            on_error=func_error,
            on_progress=func_progress,
            req_body=mp,
            req_headers={"Content-Type": mp.content_type},
            verify=False,
        )


class ImageQuery:
    def __init__(self, widget):
        self.widget = widget

    def get_image_for(self, query):
        SEARCH_URL = create_url(
            "https://www.googleapis.com/customsearch/v1?",
            key="API_KEY_HERE",  # TODO Initialize API key
            cx="CSE_ID_HERE",  # TODO Initialize CSE ID
            q=query,
            searchType="image",
        )

        UrlRequest(
            SEARCH_URL,
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
