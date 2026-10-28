from datetime import datetime
from app.casting import day_pillar, hour_pillar, cast_birth, solar_term_utc


def test_reference_day_is_jiazi():
    assert day_pillar(datetime(2000,1,7,12)).text == '甲子'

def test_23_boundary_changes_day():
    assert day_pillar(datetime(2000,1,7,22,59)).text == '甲子'
    assert day_pillar(datetime(2000,1,7,23,0)).text == '乙丑'

def test_hour_stem_for_jia_day():
    dp=day_pillar(datetime(2000,1,7,12))
    assert hour_pillar(datetime(2000,1,7,0,30),dp).text == '甲子'
    assert hour_pillar(datetime(2000,1,7,14,0),dp).text == '辛未'

def test_known_2000_chart_near_120E():
    # Use longitude 120 and Asia/Shanghai; true-solar correction does not cross a pillar boundary here.
    r=cast_birth(datetime(2000,1,7,14,0),120.0,'Asia/Shanghai','female')
    fp=r['four_pillars']
    assert fp['year']['text']=='己卯'
    assert fp['month']['text']=='丁丑'
    assert fp['day']['text']=='甲子'
    assert fp['hour']['text']=='辛未'

def test_lichun_is_early_february():
    dt=solar_term_utc(2026,'立春',315)
    assert dt.month==2 and 3 <= dt.day <= 5
