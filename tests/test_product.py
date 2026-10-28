from app.product import calculate_product, resolve_location, InputError

def test_product_city_input():
    p={'birth':{'year':2000,'month':1,'day':7,'hour':14,'minute':30,'gender':'male'},'location':{'city':'杭州市'},'options':{'target_year':2026}}
    r=calculate_product(p)
    assert r['engine']['version']=='5.8-COSMIC-WEB'
    assert r['geo']['iana_timezone']=='Asia/Shanghai'
    assert r['four_pillars']['day']['text']=='甲子'
    assert 'liu_nian' in r

def test_resolved_location_passthrough():
    r=resolve_location({'longitude':121.5,'latitude':25.0,'iana_timezone':'Asia/Taipei'})
    assert r['source']=='provided' and r['longitude']==121.5


def test_multiple_offline_places_switch():
    cases=[('温州市','Asia/Shanghai'),('建德市','Asia/Shanghai'),('台中市','Asia/Taipei'),('东京','Asia/Tokyo')]
    for city,tz in cases:
        r=resolve_location({'city':city})
        assert r['iana_timezone']==tz

def test_cosmic_ui_contains_core_sections():
    from pathlib import Path
    html=Path('web/index.html').read_text(encoding='utf-8')
    for text in ['八字命盘','喜用神分析','本命手串方案','大运时间轴','流年手串方案','流年方位']:
        assert text in html
    assert '缺' not in html

def test_cosmic_ui_starts_blank_and_has_reset():
    from pathlib import Path
    html=Path('web/index.html').read_text(encoding='utf-8')
    assert 'id="y" value=' not in html
    assert 'id="city" value="杭州市"' in html
    assert 'id="run"' in html
    assert 'id="reset"' in html
    assert "$('run').onclick=go" in html

def test_wenzhou_full_address_offline_fallback():
    p={'birth':{'year':1992,'month':11,'day':19,'hour':18,'minute':35,'gender':'male'},'location':{'city':'浙江温州市鹿城区信河街'},'options':{'target_year':2026}}
    r=calculate_product(p)
    assert r['geo']['source']=='offline_fallback'
    assert r['geo']['iana_timezone']=='Asia/Shanghai'
