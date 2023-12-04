from android import activity
from jnius import autoclass, cast

PythonActivity = autoclass("org.kivy.android.PythonActivity")
File = autoclass("java.io.File")
Environment = autoclass("android.os.Environment")
SimpleDateFormat = autoclass("java.text.SimpleDateFormat")
Date = autoclass("java.util.Date")
Context = autoclass("android.content.Context")
Intent = autoclass("android.content.Intent")
MediaStore = autoclass("android.provider.MediaStore")
FileProvider = autoclass("android.support.v4.content.FileProvider")
Uri = autoclass("android.net.Uri")
IOException = autoclass("java.io.IOException")


class CameraAndroid:
    CAMERA_REQUEST_CODE = 1450

    def __init__(self, filename):
        self.currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
        self.filename = filename

    def take_picture(self, on_complete):
        self.on_complete = on_complete

        camera_intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)

        photo_file = None
        if (
            camera_intent.resolveActivity(
                self.currentActivity.getApplicationContext().getPackageManager()
            )
            is not None
        ):
            photo_file = self._create_image_file()

            if photo_file is not None:
                photo_uri = FileProvider.getUriForFile(
                    self.currentActivity.getApplicationContext(),
                    self.currentActivity.getApplicationContext().getPackageName(),
                    photo_file,
                )

                activity.bind(on_activity_result=self.on_activity_result)

                parcelable = cast("android.os.Parcelable", photo_uri)
                camera_intent.putExtra(MediaStore.EXTRA_OUTPUT, parcelable)

                self.currentActivity.startActivityForResult(
                    camera_intent, self.CAMERA_REQUEST_CODE
                )

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == self.CAMERA_REQUEST_CODE:
            activity.unbind(on_activity_result=self.on_activity_result)
            self.on_complete(self.image_path)

    def _create_image_file(self):
        storage_dir = Context.getExternalFilesDir(Environment.DIRECTORY_PICTURES)

        image = File.createTempFile(self.filename, ".jpg", storage_dir)

        self.image_path = image.getAbsolutePath()

        return image
