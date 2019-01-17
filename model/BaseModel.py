from peewee import *
from playhouse.signals import *

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy

    @staticmethod
    def Init(database):
        database_proxy.initialize(database)
