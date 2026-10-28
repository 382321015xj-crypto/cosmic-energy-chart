from pathlib import Path

def test_cosmic54_layout_and_bracelet_canvas():
    s=(Path(__file__).parents[1]/"web"/"index.html").read_text()
    assert "align-items:start" in s
    assert "braceletCanvas" in s
    assert "drawBracelet" in s
    assert "<canvas" in s
    assert "图片仅做示意参考" in s
    assert "第一喜用主绳" in s
