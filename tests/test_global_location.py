import json
from unittest.mock import patch
from app import location

def fake_urlopen(req, timeout=12):
    class R:
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def read(self):
            return json.dumps([
              {'place_id':1,'display_name':'Cambridge, Cambridgeshire, England, United Kingdom','lon':'0.1218','lat':'52.2053','address':{'country_code':'gb'},'type':'city'},
              {'place_id':2,'display_name':'Cambridge, Massachusetts, United States','lon':'-71.1056','lat':'42.3751','address':{'country_code':'us'},'type':'city'}
            ]).encode()
    return R()

def test_global_search_returns_candidates(monkeypatch,tmp_path):
    monkeypatch.setattr(location,'CACHE_FILE',tmp_path/'cache.json')
    monkeypatch.setattr(location,'timezone_for',lambda lon,lat,country_code='':'Europe/London' if float(lon)>0 else 'America/New_York')
    with patch('urllib.request.urlopen',fake_urlopen):
        rows=location.search_locations('Cambridge',5)
    assert len(rows)==2
    assert rows[0]['iana_timezone']=='Europe/London'
    assert rows[1]['iana_timezone']=='America/New_York'

def test_global_cache_avoids_second_network(monkeypatch,tmp_path):
    monkeypatch.setattr(location,'CACHE_FILE',tmp_path/'cache.json')
    monkeypatch.setattr(location,'timezone_for',lambda lon,lat,country_code='':'Europe/London')
    with patch('urllib.request.urlopen',fake_urlopen): location.search_locations('Cambridge',5)
    with patch('urllib.request.urlopen',side_effect=AssertionError('network should not be used')):
        assert location.search_locations('Cambridge',5)

def test_historical_dst_zoneinfo():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ny=ZoneInfo('America/New_York')
    summer=datetime(1992,7,1,12,0,tzinfo=ny)
    winter=datetime(1992,1,1,12,0,tzinfo=ny)
    assert summer.utcoffset()!=winter.utcoffset()
