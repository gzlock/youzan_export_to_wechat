import json
import os

import requests

from services.item import Item


class WeChatToken:
    def __init__(self, json_string):
        # print('微信 token', json_string)
        data = json.loads(json_string)
        if 'errmsg' in data:
            raise Exception(data['errmsg'])
        self.token = data['access_token']


WeChat_Base_Url = 'https://api.weixin.qq.com/scan/product/v2/'


class WeChat:
    __AppID = ''
    __AppSecret = ''
    __Token = ''
    __page_context = ''

    def __init__(self, AppID: str, AppSecret: str):
        print('wechat __init__')
        WeChat.__AppID = AppID
        WeChat.__AppSecret = AppSecret
        WeChat.getToken()

    @staticmethod
    def getToken():
        data = requests.get(
            url='https://api.weixin.qq.com/cgi-bin/token',
            params={'grant_type': 'client_credential', 'appid': WeChat.__AppID, 'secret': WeChat.__AppSecret})
        WeChat.__Token = WeChatToken(data.text).token
        # print('微信token', WeChat.__Token)

    @staticmethod
    def exec(command: str, params: {}):
        WeChat.getToken()  # 防止 token 过期
        url = WeChat_Base_Url + command
        json_content = json.dumps(params, ensure_ascii=False).encode('utf-8')
        data = requests.post(url, params={'access_token': WeChat.__Token},
                             headers={'Content-Type': 'application/json'},
                             data=json_content)
        # print('wechat exec', command, data.text)
        return data.json()

    @staticmethod
    def GetItemByPage(page_num: int, page_size: int):
        res = WeChat.__getItems(page_num=page_num, page_size=page_size)
        print('wechat item page', page_num, len(res['product']))
        return [Item.FromWeChat(item) for item in res['product']]

    @staticmethod
    def GetItems():
        _list = []
        page_num = 1
        page_size = 100

        if hasattr(os.environ, 'DEV') and os.environ['DEV'] == '1' == '1':
            page_size = 1

        while 1:
            res = WeChat.GetItemByPage(page_num=page_num, page_size=page_size)
            res_len = len(res)
            _list.extend(res)
            if res_len < page_size:
                break
            page_num += 1
            continue

        return _list

    @staticmethod
    def __getItems(page_num: int, page_size: int = 1):
        command = 'getinfobypage'
        params = {'page_num': page_num, 'page_size': page_size}
        if page_num > 1:
            params['page_context'] = WeChat.__page_context
        res = WeChat.exec(command, params)
        WeChat.__page_context = res['page_context']
        return res


class WeChatImportStatus:
    def __init__(self, data: dict):
        result = data['result']
        # self.success = result['succ_cnt']
        # self.fail = result['fail_cnt']
        self.isSuccess = False
        if 'statuses' in result and isinstance(result['statuses'], list) and len(result['statuses']) > 0:
            self.message = result['statuses'][0]['err_msg_zh_cn']
            self.isSuccess = result['statuses'][0]['ret'] == 0
        else:
            self.message = '成功'

    def __str__(self):
        return self.message
