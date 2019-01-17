import json

from peewee import *

from model.BaseModel import BaseModel


class Config(BaseModel):
    key = CharField(unique=True)
    value = CharField()

    @staticmethod
    def Set(key: str, value):

        if hasattr(value, '__dict__'):
            value = vars(value)

        value = json.dumps(value, ensure_ascii=False)

        try:
            res = Config.get(Config.key == key)
            res.value = value
            res.save()
        except:
            res = Config.create(key=key, value=value)

        return res

    @staticmethod
    def Get(key, default=None):
        res = default
        try:
            data = Config.get(Config.key == key)
            res = json.loads(data.value)
        except:
            pass

        return res
