class WeChatItemCategory:
    def __init__(self, name):
        self.name = name

    def __dict__(self):
        return {'category_item': self.name}

    @staticmethod
    def FromStringList(array):
        result = []
        for item in array:
            result.append(WeChatItemCategory(item))
        return result
