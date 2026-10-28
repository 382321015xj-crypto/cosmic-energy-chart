from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'web'/'index.html').read_text('utf-8')
def test_new_verified_combinations_are_wired():
    assert "'水_火_木':'/assets/bracelet_auth_water_fire_wood.jpg'" in HTML
    assert "'水_木_火':'/assets/bracelet_auth_water_wood_fire.jpg'" in HTML
    assert "'火_土_金':'/assets/bracelet_auth_natal_fire_earth_metal.jpg'" in HTML
    assert (ROOT/'web/assets/bracelet_auth_water_fire_wood.jpg').exists()
    assert (ROOT/'web/assets/bracelet_auth_water_wood_fire.jpg').exists()
def test_visual_key_is_role_order_not_natal_annual_prefix():
    assert 'let combo=`${a}_${b}_${c}`' in HTML
    assert 'authentic[combo]' in HTML
