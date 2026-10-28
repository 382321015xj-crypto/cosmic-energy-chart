from datetime import datetime
from pprint import pprint
from app.casting import cast_birth
from app.dayun import build_dayun

birth=datetime(2000,1,7,14,0)
r=cast_birth(birth,120.0,'Asia/Shanghai','female')
r['da_yun']=build_dayun(birth,'Asia/Shanghai',r['four_pillars']['month']['text'],r['four_pillars']['year']['stem'],'female')
pprint(r,sort_dicts=False)
