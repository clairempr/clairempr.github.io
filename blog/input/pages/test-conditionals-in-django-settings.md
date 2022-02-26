# Testing Conditionals in the Django Settings File

#### Testing conditionals in the Django settings file  

## Posted Feb. 25, 2022

I have an old Django project where I'm working on achieving 100% unit test coverage to prepare for a major overhaul, so I find myself writing unit tests for the sorts of things that Django developers might not normally get around to. Recently I was struggling to test a situation in my Django settings file where I have GeoDjango-related settings that are different for Windows than they are for Linux. I run the application under Docker myself, so it's always Linux, but I wanted to leave these settings intact for now. 

```python
# Where to find SpatiaLite and GDAL libraries, necessary to support geodatabase stuff in SQLite
if platform.system() == 'Windows':
    # For Windows, use the following setting. Get mod_spatialite from http://www.gaia-gis.it/gaia-sins/
    # Put all DLLs in the same directory with the Python executable (system and probably also virtualenv)
    SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
    # For Windows, set the location of the GDAL DLL and add the GDAL directory to your PATH for the other DLLs
    # Under Linux it doesn't seem to be necessary
    GDAL_LIBRARY_PATH = 'C:\Program Files\GDAL\gdal201.dll'
    # A Fallback
    DB_DIR = BASE_DIR
else:
    # For Linux
    SPATIALITE_LIBRARY_PATH = '/usr/local/lib/mod_spatialite.so'
```

I knew how to mock platform.system(), but I was tearing my hair out trying to figure out how to test both conditions. The settings had already been loaded by the time the testrunner got to my tests, so whatever was set at the time was what I got. After a lot of googling, and combing Stack Overflow and various blog entries, I came to the conclusion that this isn't something that people really test, or at least not often.

An unanswered [question on Stack Overflow](https://stackoverflow.com/questions/62582344/testing-django-settings-behavior-with-unittest-and-python) pointed me to `importlib.reload`, so I gave it a shot. The settings file was imported in my test file as `from django.conf import settings`, which is how the Django docs say that it should be done. This is how I usually import it too, but I got the following error with `importlib.reload(settings)`:

```

======================================================================
ERROR: test_settings_for_linux (letterpress.tests.test_settings.TestSettingsForLinuxTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/local/lib/python3.5/unittest/mock.py", line 1159, in patched
    return func(*args, **keywargs)
  File "/code/letterpress/tests/test_settings.py", line 29, in test_settings_for_linux
    importlib.reload(settings)
  File "/usr/local/lib/python3.5/importlib/__init__.py", line 139, in reload
    raise TypeError("reload() argument must be a module")
TypeError: reload() argument must be a module

```
Clearly that wasn't the way to go. After a lot of trial and error and taking another look at that Stack Overflow question, I found the solution. If I imported my application's Django settings directly (i.e. `import letterpress.settings`), I finally got reloading the settings to work by using `importlib.reload(letterpress.settings)`. 

Here's the finished product, using `patch` to switch between Linux and Windows:
 
```python
import importlib

from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

# Normally Django settings should be imported as "from django.conf import settings"
# but here we need to import our settings module explicitly so we can manually reload it
import letterpress.settings

class TestGeoDjangoSettingsTestCase(SimpleTestCase):
    """
    SPATIALITE_LIBRARY_PATH and GDAL_LIBRARY_PATH settings
    should be different for Linux and Windows
    """

    @patch('platform.system', autospec=True)
    def test_settings_for_linux(self, mock_system):
        """
        GDAL_LIBRARY_PATH should be set for Windows only
        If platform.system() returns something else, settings.GDAL_LIBRARY_PATH shouldn't be set
        """

        # Mock platform.system() to have it return 'Linux'
        mock_system.return_value = 'Linux'

        # Reload Django settings
        importlib.reload(letterpress.settings)

        self.assertTrue(letterpress.settings.SPATIALITE_LIBRARY_PATH.endswith('.so'),
                        "On Linux, SPATIALITE_LIBRARY_PATH should end with '.so'")

        with self.assertRaises(AttributeError):
            print(letterpress.settings.GDAL_LIBRARY_PATH)

    @patch('platform.system', autospec=True)
    def test_settings_for_windows(self, mock_system):
        """
        GDAL_LIBRARY_PATH should be set for Windows only
        If platform.system() returns 'Windows', settings.GDAL_LIBRARY_PATH should be set
        """

        # Mock platform.system() to have it return 'Windows'
        mock_system.return_value = 'Windows'

        # Reload Django settings
        importlib.reload(letterpress.settings)

        self.assertFalse(letterpress.settings.SPATIALITE_LIBRARY_PATH.endswith('.so'),
                         "On Windows, SPATIALITE_LIBRARY_PATH should not end with '.so'")

        self.assertFalse(letterpress.settings.GDAL_LIBRARY_PATH == None,
                         'On Windows, GDAL_LIBRARY_PATH should be set')
```


