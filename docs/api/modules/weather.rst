:mod:`Weather` --- Fetch weather data by ZIP code
=================================================

Commands
--------

.. cmdoption:: .weather <location>
.. cmdoption:: .w <location>

    Fetch weather for a location. If no location is passed, the user's 
    preferred location will be used.
    
    Example: ``.w 95051``

.. cmdoption:: .setloc <location>

    Set your preferred location
    
    Example: ``.setloc Rochester, NY``, ``.setloc 14623``


.. cmdoption:: .wunit <type>

    Set your preference between fahrenheit or celsius.
    
    Example: ``.setloc F``

Class Reference
---------------

.. automodule:: pyircbot.modules.Weather
    :members:
    :undoc-members:
    :show-inheritance:
