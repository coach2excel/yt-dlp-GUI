
from urllib import parse
import json
#使用json，可以自动检测编码，但需要注意的是，它返回的是python对象，不一定是字符串

def convert_xe(s):

    if r'\x' in s:
        s= s.encode('unicode_escape')
        ss = s.decode('utf-8').replace('\\x','%')
        cn = parse.unquote(ss)
        #cn = cn.decode('utf-8')	
        return cn
    else:
        return s


if __name__ == '__main__':
    s = r"xb7\xec\xb8\xc9\xc9\xe6ʵ\xd1\xe9\xbe\xcd\xcaǸ\xf6BUG\xa3\xacֻΪ\xc8\xc3\xc4㶴Ϥ\xd5\xe2\xb8\xf6\xd3\xee\xd6\xe6\xb5ı\xbe\xd6ʣ\xa1.f140.m4a"
    print(convert_xe(s))
