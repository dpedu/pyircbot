:mod:`Weather` --- Fetch weather data by ZIP code
=================================================

Commands
--------

 - *.weather <location>*, *.w <location>* - fetch weather for a locaiton. If no location is passed, the user's preferred location will be used.
    Example: *.w 95051*
 - *.setloc <location>* - set your preferred location
    Example: *.setloc Rochester, NY*
    *.setloc 14623*
 - *.wunit <type>* - set your preference between fahrenheit or celsius.
    Example: *.setloc F*

Class Reference
---------------

.. automodule:: pyircbot.modules.Weather
    :members:
    :undoc-members:
    :show-inheritance:
