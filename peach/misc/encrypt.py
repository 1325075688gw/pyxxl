import hashlib
from datetime import datetime

from Crypto import Random
from Crypto.Cipher import AES, DES3, DES

BS = 16


def pad(s, bs=BS):
    """
    pkcs7padding
    """
    return s + (bs - len(s) % bs) * chr(bs - len(s) % bs).encode()


def unpad(s):
    """
    de_pkcs7padding
    """
    return s[0 : -s[-1]]


class AESCipher:
    """
    注意: CBC模式每次加密时需要重新实例化一个cipher对象来重置IV，不然相同的数据每次加密结果都会不一样
    """

    def __init__(self, key, mode=AES.MODE_ECB, IV=None):
        self.key = key
        self.mode = mode
        self.IV = IV
        if self.mode == AES.MODE_CBC:
            assert self.IV
            self.cipher = AES.new(self.key, self.mode, self.IV)
        else:
            self.cipher = AES.new(self.key, self.mode)

    def encrypt(self, raw):
        return self.cipher.encrypt(pad(raw))

    def decrypt(self, enc):
        return unpad(self.cipher.decrypt(enc))


class AESCBCCipher:
    """
    与上面的实现区别在于偏移量IV不需要配置而是随机生成，所以无法用于数据库的查询
    """

    def __init__(self, key):
        """
        :param key: 256位bits，即32长度bytes.
        """
        self.bs = AES.block_size
        self.key = key

    def encrypt(self, raw):
        """
        :param raw: bytes类型
        :return:
        """
        iv = Random.new().read(self.bs)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(pad(raw, self.bs))

    def decrypt(self, enc):
        cipher = AES.new(self.key, AES.MODE_CBC, enc[: self.bs])
        return unpad(cipher.decrypt(enc[self.bs :]))


class DESCipher:
    """
    DES 加解密封装
    """

    def __init__(self, key, mode=DES.MODE_ECB, bs=8):
        self.key = key
        self.mode = mode
        self.bs = bs

    def encrypt(self, raw):
        cipher = DES.new(self.key, self.mode)
        return cipher.encrypt(pad(raw, self.bs))

    def decrypt(self, enc):
        cipher = DES.new(self.key, self.mode)
        return unpad(cipher.decrypt(enc))


class DES3Cipher:
    """
    DES3 加解密封装
    """

    def __init__(self, key):
        self.key = key

    def encrypt(self, raw, bs=16):
        """
        :param raw: 需加密的bytes数据
        :param bs: block size
        :return: 加密后的bytes密文
        """
        cipher = DES3.new(self.key, DES3.MODE_ECB)
        return cipher.encrypt(pad(raw, bs))

    def decrypt(self, enc):
        """
        :param enc: 加密后的bytes密文
        :return: 解密后的bytes数据
        """
        cipher = DES3.new(self.key, DES3.MODE_ECB)
        return unpad(cipher.decrypt(enc))


def md5_digest(raw, key=None):
    m = hashlib.md5()
    m.update(raw)
    if key:
        m.update(key)
    return m.digest()


def md5(data_str: str, key: str = None) -> str:
    m = hashlib.md5()
    m.update(data_str.encode("utf-8"))
    if key:
        m.update(key.encode("utf-8"))
    return m.hexdigest()


if __name__ == "__main__":
    access_code = "4209b303210ee9d3"

    now = datetime.now()
    ts = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    des3_coder = DES3Cipher(access_code.encode("utf-8"))

    a = des3_coder.encrypt(ts.encode())
    print(a)

    print(des3_coder.decrypt(a))
