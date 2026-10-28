from datetime import datetime
from app.dayun import dayun_direction, build_dayun

def test_direction_rules():
    assert dayun_direction('甲','male')=='forward'
    assert dayun_direction('乙','female')=='forward'
    assert dayun_direction('乙','male')=='reverse'
    assert dayun_direction('甲','female')=='reverse'

def test_dayun_has_ten_cycles():
    r=build_dayun(datetime(2000,1,7,14),'Asia/Shanghai','丁丑','己','female')
    assert len(r['cycles'])==10
