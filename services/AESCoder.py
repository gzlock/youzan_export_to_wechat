from Crypto.Cipher import AES


class AESCoder:
    __Key__ = None
    __Mode__ = AES.MODE_CBC
    __Length__ = 16

    def __init__(self, key):
        AESCoder.__Key__ = key.encode('utf-8')

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    @staticmethod
    def encrypt(text):
        text = text.encode('utf-8')
        cryptor = AES.new(AESCoder.__Key__, AESCoder.__Mode__, b'0000000000000000')
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 16
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        elif count > length:
            add = (length - (count % length))
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return cryptor.encrypt(text)

    # 解密后，去掉补足的空格用strip() 去掉
    @staticmethod
    def decrypt(text):
        cryptor = AES.new(AESCoder.__Key__, AESCoder.__Mode__, b'0000000000000000')
        plain_text = cryptor.decrypt(text)
        # return plain_text.rstrip('\0')
        return bytes.decode(plain_text).rstrip('\0')
