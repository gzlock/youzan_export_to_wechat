import json

from services.youzan import YouZanCategories, YouZanCategory

LinkUrl = 'pages/goods/detail/index?alias='


class Item:
    def __init__(self, id, title: str, desc: str, price: int, ori_price: int, stock: int,
                 images: [],
                 skus: [],
                 official_category_list: list,
                 category_list: list,
                 link_url: str,
                 onSale: bool = True,
                 book=None, ):
        self.id = str(id)
        self.title = title
        self.link_url = link_url
        self.desc = desc
        self.price = price
        self.ori_price = ori_price  # 原价
        self.images = images
        self.skus = skus
        self.book = book
        self.official_category_list = official_category_list  # 微信官方分类
        self.category_list = category_list  # 自定义分类
        self.stock = stock
        self.on_sale = onSale  # 上架状态

    def __str__(self):
        return self.title

    def setOfficialCategory(self, name: str):
        self.official_category_list = [{'category_name': name}]

    def toWeChatItem(self, wechat_app_id: str):
        sale_status = 'on'
        if self.stock == 0 or not self.on_sale:
            sale_status = 'off'

        image_list = []
        official_category_list = self.official_category_list
        category_list = self.category_list
        sku_list = []

        if len(category_list) == 0:
            category_list = official_category_list

        # 处理 图片
        for img in self.images:
            image_list.append({'url': img})

        # 处理 sku
        for sku in self.skus:
            sku_list.append(sku.ToWeChatSku(self))

        data = {
            "pid": 'youzan_' + self.id,
            "image_info": {  # 商品图片
                "main_image_list": image_list
            },
            'category_info': {  # 自定义的分类
                'category_item': category_list,
            },
            'official_category_info': {  # 微信 官方指定的分类
                'category_item': official_category_list,
            },
            'link_info': {
                "url": self.link_url,
                "wxa_appid": wechat_app_id,  # todo 小程序 appid
                'link_type': 'wxa'
            },
            'title': self.title,  # 最长 30字 标题
            'sub_title': self.title,  # todo 最长 30字 副标题
            'brand': '',  # todo 商品品牌
            'shop_info': {
                "source": 2
            },
            'desc': self.title,  # 最长 300字 简介
            'price_info': {  # 价格信息
                'min_price': self.price / 100,  # 现有最低价
                'max_price': self.price / 100,  # 现在最高价
                'min_ori_price': self.ori_price / 100,  # 原价最低价
                'max_ori_price': self.ori_price / 100,  # 原价最高价
            },
            'sale_info': {  # 销售信息
                'sale_status': sale_status,  # 是否上架
                'stock': self.stock  # 库存数量
            },
            'sku_info': {
                'sku_item': sku_list
            },
            'partial_update': 0
        }
        if self.book is not None:
            data['custom_info'] = {'custom_list': [
                {'key': 'publisher', 'value': self.book['publisher']},
                {'key': 'author', 'value': self.book['author']},
                {'key': 'book_desc', 'value': self.book['desc']},
            ]}
        return data

    @staticmethod
    def FromYouZan(data: dict):
        images = []
        for img in data['item_imgs']:
            images.append(img['url'])

        skus = []
        sku_images = []
        if 'sku_images' in data:
            sku_images = data['sku_images']

        if 'skus' in data:
            for sku in data['skus']:
                skus.append(Sku.FromYouZan(alias=data['alias'], data=sku, sku_images=sku_images))

        category_list = []
        # 处理 自定义 分类
        youzanCategory: YouZanCategory = YouZanCategories.List[data['cid']]
        temp_categories = [youzanCategory]
        parent: YouZanCategory = youzanCategory.parent
        while parent is not None:
            temp_categories.insert(0, parent)
            parent = parent.parent

        for c in temp_categories:
            category_list.append({'category_name': c.name})

        return Item(link_url=LinkUrl + data['alias'],
                    id=data['item_id'],
                    title=data['title'],
                    desc=data['desc'],
                    stock=data['quantity'],
                    price=data['price'],
                    ori_price=data['price'],
                    images=images,
                    skus=skus,
                    onSale=data['is_listing'],
                    official_category_list=[],
                    category_list=category_list,
                    )

    @staticmethod
    def FromWeChat(data: dict):
        skus = []
        images = []
        for img in data['image_info']['main_image_list']:
            images.append(img['url'])
        official_category_list = []
        category_list = []

        for category in data['official_category_info']['category_item']:
            official_category_list.append(category)

        for category in data['category_info']['category_item']:
            category_list.append(category)

        if 'sku_info' in data and 'sku_item' in data['sku_info'] and len(
                data['sku_info']['sku_item']) > 0:
            for item in data['sku_info']['sku_item']:
                images = []
                for image in item['image_info']['main_image_list']:
                    images.append(image['url'])
                skus.append(Sku(
                    link_url=item['link_url'],
                    id=item['sku_id'],
                    price=int(float(item['price_info']['min_price']) * 100),
                    ori_price=int(float(item['price_info']['min_ori_price']) * 100),
                    images=images,
                    stock=item['sale_info']['stock']
                ))

        book = None
        if 'custom_info' in data and 'custom_list' in data['custom_info'] and len(
                data['custom_info']['custom_list']) > 0:
            book = {}
            for item in data['custom_info']['custom_list']:
                if item['key'] == 'publisher':
                    book['publisher'] = item['value']
                elif item['key'] == 'author':
                    book['author'] = item['value']
                elif item['key'] == 'book_desc':
                    book['desc'] = item['value']

        on_sale = data['sale_info']['sale_status'] == 'on'

        return Item(link_url=data['link_info']['url'],
                    id=str.replace(data['pid'], 'youzan_', ''),
                    title=data['title'],
                    desc=data['desc'],
                    price=data['price_info']['min_price'] * 100,
                    ori_price=data['price_info']['min_ori_price'] * 100,
                    stock=data['sale_info']['stock'],
                    images=images,
                    skus=skus,
                    book=book,
                    official_category_list=official_category_list,
                    category_list=category_list,
                    onSale=on_sale
                    )


class Sku:
    def __init__(self, id, price: int, ori_price: int, stock: int, images: [],
                 link_url: str,
                 k_title: str = None,
                 v_title: str = None, ):
        self.id = id
        self.link_url = link_url
        self.k_title = k_title
        self.v_title = v_title
        self.price = price
        self.ori_price = ori_price  # 原价
        self.stock = stock
        self.images = images

    def ToWeChatSku(self, item: Item = None):
        image_list = []
        if len(image_list) == 0 and item is not None:
            image_list.append({'url': item.images[0]})
        else:
            for image in self.images:
                image_list.append({'url': image})

        stock = item.stock if self.stock > item.stock else self.stock
        sale_status = 'on' if stock > 0 else 'off'

        return {
            'sku_id': self.id,
            'image_info': {'main_image_list': image_list},
            'link_url': self.link_url,  # todo 小程序 页面 路径和参数 /a?id=123
            'price_info': {
                'min_price': self.price / 100,
                'max_price': self.price / 100,
                'min_ori_price': self.ori_price / 100,
                'max_ori_price': self.ori_price / 100,
            },
            'sale_info': {
                "sale_status": sale_status,
                "stock": stock,
            },
            'shop_info': {
                "source": 2
            }
        }

    @staticmethod
    def FromYouZan(alias: str, data: dict, sku_images: []):
        images = []
        properties = json.loads(data['properties_name_json'])
        kid = properties[0]['kid']  # 规格id
        k = properties[0]['k']  # 规格名称

        vid = properties[0]['vid']  # 细分 规格id
        v = properties[0]['v']  # 细分 规格名称

        for img in sku_images:
            if img['k_id'] == kid and img['v_id'] == vid:
                images.append(img['img_url'])

        return Sku(link_url=LinkUrl + alias,
                   id=data['sku_unique_code'],
                   price=data['price'],
                   ori_price=data['price'],
                   stock=data['quantity'],
                   images=images,
                   k_title=k,
                   v_title=v,
                   )
