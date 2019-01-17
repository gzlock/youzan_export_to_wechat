from youzan.yzclient import YZClient


class YouZanItem:
    def __init__(self, _id: int, title: str, alias: str, category: str = None, book: dict = None):
        self.id = str(_id)
        self.title = title
        self.alias = alias
        self.category = category
        self.book = book

    def __str__(self):
        return self.title

    # 解析JSON
    @staticmethod
    def ParseList(data: dict):
        # {'error_response': {'code': 40002, 'msg': '参数 client_id 不正确'}}
        if 'error_response' in data:
            raise Exception(data['error_response']['msg'])
        response = data['response']
        items = response['items']
        result = []
        for item in items:
            result.append(YouZanItem(_id=item['item_id'], title=item['title'], alias=item['alias']))

        return result


class YouZanCategory:
    def __init__(self, cid: int, name: str, parent=None):
        self.cid = cid
        self.name = name
        self.parent = parent


class YouZanCategories:
    List = {}

    # 读取有赞的官方分类，并且初始化
    def __init__(self):
        YouZanCategories.List.clear()
        data = YZClient.exec('youzan.itemcategories.get', '3.0.0', 'GET')
        categories = data['response']['categories']
        for c in categories:
            category = YouZanCategory(cid=c['cid'], name=c['name'])
            YouZanCategories.List[c['cid']] = category
            if c['sub_categories']:
                YouZanCategories.__CreateCategory(category, c['sub_categories'])

    @staticmethod
    def __CreateCategory(parent: YouZanCategory, sub_categories: list):
        for c in sub_categories:
            if c['cid'] in YouZanCategories.List:
                continue

            category = YouZanCategory(parent=parent, cid=c['cid'], name=c['name'])
            YouZanCategories.List[c['cid']] = category
            if c['sub_categories']:
                YouZanCategories.__CreateCategory(category, c['sub_categories'])
