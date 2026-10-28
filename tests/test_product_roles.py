from app.engine import _role_piece

def test_fire_role_is_not_red_cord_when_used_as_bead():
    assert '红色编织绳' == _role_piece('火','cord')['materials'][0]
    bead = _role_piece('火','primary_bead')['materials'][0]
    assert bead in ('南红玛瑙','红玛瑙','石榴石')
    assert '绳' not in bead

def test_earth_and_wood_role_materials():
    assert '编织绳' in _role_piece('土','cord')['materials'][0]
    assert _role_piece('土','primary_bead')['materials'][0] == '虎眼石'
    assert _role_piece('木','secondary_bead')['materials'][0] == '绿松石'
