import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import cosmic6

def test_yijing_cast_has_six_lines():
    result = cosmic6.cast_yijing({"question":"测试事项"})
    assert len(result["lines_bottom_to_top"]) == 6
    assert all(x["value"] in (6,7,8,9) for x in result["lines_bottom_to_top"])
    assert all(x["moving"] == (x["value"] in (6,9)) for x in result["lines_bottom_to_top"])

def test_huangdaxian_draw_is_marked_data_required():
    result = cosmic6.draw_lingqian({"category":"财运财富","series":"黄大仙灵签","days":7})
    assert 1 <= result["number"] <= 100
    assert result["status"] == "SIGN_TEXT_DATA_REQUIRED"

def test_annual_flying_star_2026_center_one():
    result = cosmic6.fengshui_flying_stars({"facing_degrees":180,"built_year":2020,"target_year":2026})
    assert result["annual_center_star"] == 1
    assert len(result["palaces"]) == 9
    assert sorted(result["palaces"].values()) == list(range(1,10))

def test_bad_yijing_question_rejected():
    try:
        cosmic6.cast_yijing({"question":" "})
    except ValueError:
        return
    assert False, "empty question should fail"
