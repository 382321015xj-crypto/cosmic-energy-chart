from pathlib import Path

def test_cosmic562_ui_requirements():
    root=Path(__file__).parents[1]
    s=(root/'web'/'index.html').read_text(encoding='utf-8')
    for x in ['2000-01-01','00:01','浙江省','杭州市','cosmic_landscape_pure.jpg','忌神 / 搭配禁用','暂无经过材质一致性核验的实物图']:
        assert x in s
    assert 'cosmic_bottom_clean.jpg' not in s
    assert 'cosmic_top_clean.jpg' not in s
    assert "natal_火_土_金" in s and "annual_土_火_金" in s
    assert (root/'web'/'assets'/'bracelet_auth_natal_fire_earth_metal.jpg').exists()
    assert (root/'web'/'assets'/'bracelet_auth_annual_earth_fire_metal.jpg').exists()
