from app.engine import *
from datetime import datetime

def test_hidden_total():
    for b,d in HIDDEN.items(): assert abs(sum(d.values())-1)<1e-9

def test_initial_total():
    p=[Pillar('甲','子'),Pillar('丙','寅'),Pillar('戊','辰'),Pillar('庚','申')]
    assert abs(sum(element_initial(p).values())-800)<1e-9

def test_true_solar_at_meridian():
    r=true_solar_time(datetime(2000,1,1,12),120,8)
    assert r['longitude_correction_minutes']==0

def test_pipeline():
    p=[Pillar('庚','午'),Pillar('甲','申'),Pillar('甲','子'),Pillar('丙','寅')]
    r=calculate_from_pillars(p)
    assert len(r['yong_shen']['first'])==1
    assert r['mapping']['wear_hand']=='左手'

def test_yongshen_not_lowest_element_rule():
    # A winter chart: fire can rank high because of climate/support logic, not because it is simply lowest.
    p=[Pillar('壬','申'),Pillar('辛','亥'),Pillar('己','亥'),Pillar('癸','酉')]
    r=calculate_from_pillars(p)
    assert '不采用缺什么补什么' in r['yong_shen']['selection_principle']
    assert r['yong_shen']['decision_trace']
