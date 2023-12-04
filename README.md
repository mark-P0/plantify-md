# PlantifyMD

<!-- Mobile plant identifier with KivyMD and Pl@ntNet -->

Identify plant images in Python and KivyMD using the Pl@ntNet API

## Dependencies
> Versions unfortunately not pinned

- Kivy ([KivyMD](https://github.com/kivymd/KivyMD))
    - Cross-platform GUI framework
    - Also provides methods for accessing Android APIs via `jnius` (`pyjnius`) and `python-for-android`
- [Pl@ntNet](https://my.plantnet.org/)
    - Plant identification API
- `requests-toolbelt`
    - For preparing a multipart encoded data
- Android camera script based on [`nipe-project` by `jefersonvinicius`](https://github.com/jefersonvinicius/nipe-project/blob/master/device/cameraandroid.py)