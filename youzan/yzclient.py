import requests

from youzan import auth


####################################
#
#   有赞开放平台SDK - Python 2.0.0
#
#      三方库依赖: requests
#
####################################


class YZClient:
    __Token = ''

    def __init__(self, authorize):
        # 获取token
        if isinstance(authorize, auth.Sign):
            token = requests.post('https://open.youzan.com/oauth/token',
                                  {'client_id': authorize.app_id, 'client_secret': authorize.app_secret,
                                   'grant_type': 'silent', 'kdt_id': authorize.kdt_id})

            token = token.json()
            if 'error_description' in token:
                raise Exception(token['error_description'])

            YZClient.__Token = token['access_token']
        else:
            YZClient.__Token = authorize.token

    @staticmethod
    def exec(apiName, version, method, params={}, files={}):
        # print('YouZan exec token', YZClient.__Token)
        http_url = 'https://open.youzan.com/api'
        service = apiName[0: apiName.rindex('.')]
        action = apiName[apiName.rindex('.') + 1: len(apiName)]

        param_map = {}
        http_url += '/oauthentry'
        param_map['access_token'] = YZClient.__Token
        param_map = {**param_map, **params}

        http_url = http_url + '/' + service + '/' + version + '/' + action

        resp = YZClient.__send_request(http_url, method, param_map, files)
        if resp.status_code != 200:
            print(resp.status_code)
            raise Exception('Invoke failed')
        return resp.json()

    @staticmethod
    def __send_request(url, method, param_map, files):
        headers_map = {
            'User-Agent': 'X-YZ-Client 2.0.0 - Python'
        }
        # print('url', url)
        if method.upper() == 'GET':
            return requests.get(url=url, params=param_map, headers=headers_map)
        elif method.upper() == 'POST':
            return requests.post(url=url, data=param_map, files=files, headers=headers_map)
