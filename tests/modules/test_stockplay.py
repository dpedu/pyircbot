import pytest
from contextlib import closing
from tests.lib import *  # NOQA - fixtures
from time import sleep, time
import datetime


@pytest.fixture
def stockbot(fakebot):
    """
    Provide a bot loaded with the Calc module. Clear the database.
    """
    fakebot.botconfig["module_configs"]["StockPlay"] = {
        "startbalance": 10000,
        "tradedelay": 0,
        "tcachesecs": 120,
        "bginterval": 45,
        "announce_trades": True,
        "announce_channel": "#trades",
        "providers": [
            {
                "provider": "iexcloud",
                "apikey": "xxxxxxxxxxxxxxxxxxxxxx",
                "background_interval": 1
            },
            {
                "provider": "alphavantage",
                "apikey": "xxxxxxxxxxxxxxxxxxxxxx",
                "background_interval": 1
            }
        ]
    }
    fakebot.loadmodule("SQLite")
    # with closing(fakebot.moduleInstances["SQLite"].opendb("remind.db")) as db:
    #     db.query("DROP TABLE IF EXISTS `reminders`;")
    # fakebot.loadmodule("Remind")

    # os.system("cp /Users/dave/code/pyircbot-work/examples/data2/data/SQLite/stockplay.db {}".format(fakebot.moduleInstances["SQLite"].getFilePath()))
    # os.system("ln -s /Users/dave/code/pyircbot-work/examples/data2/data/SQLite/stockplay.db {}".format(fakebot.moduleInstances["SQLite"].getFilePath()))

    fakebot.loadmodule("StockPlay")
    return fakebot


# @pytest.mark.slow
# def test_stockplay(stockbot):
#     sp = stockbot.moduleInstances["StockPlay"]
#     # import pdb
#     # pdb.set_trace()
#     # print(sp.cache)
#     # print(sp.cache.get_price("AmD", 60))
#     # print(sp.cache.get_price("AmD", 60))
#     # print(sp.cache.get_price("AmD", 60))
#     # print(sp.cache.get_price("nut", 60))

#     symbols = set()

#     with closing(sp.sql.getCursor()) as c:
#         for row in c.execute("SELECT * FROM stockplay_holdings").fetchall():
#             symbols.update([row["symbol"].lower()])

#     print(symbols)

#     # # symbols = "a bah chk crm cron f fb mdla nio too tsla".split()
#     for symbol in symbols:
#         p = sp.cache.get_price(symbol, 0)
#         if not p:
#             print("not supported:", symbol)
#             continue
#         print(symbol, "age: ", time() - p.time)

#     # print(sp.cache.get_price("gigl", 60))
