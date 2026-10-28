from datetime import datetime
from app.casting import cast_birth
from app.dayun import build_dayun
from app.dynamic import pillar_supply, interaction_scan, annual_pillar, dynamic_analysis

def test_pillar_supply_total_200():
    assert round(sum(pillar_supply('庚申').values()),6)==200

def test_interactions_detect_clash():
    rows=interaction_scan(['甲子','乙丑','丙寅','丁卯'],'戊辰','己午')
    assert any(r['type']=='六冲' and set(r['pair'])==set('子午') for r in rows)

def test_annual_pillar_2026():
    assert annual_pillar(2026)=='丙午'

def test_dynamic_pipeline():
    c=cast_birth(datetime(2000,1,7,14,0),120.0,'Asia/Shanghai','male')
    d=build_dayun(datetime(2000,1,7,14,0),'Asia/Shanghai',c['four_pillars']['month']['text'],c['four_pillars']['year']['stem'],'male')
    out=dynamic_analysis(c,d,2026)
    assert out['year_pillar']=='丙午'
    assert out['dynamic_state'] in {'EXPAND','BALANCED','CONSERVATIVE'}
    assert set(out['annual_mapping']) >= {'main_cord','primary_bead','secondary_bead','avoid_beads'}
