from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .full_engine import calculate_full
from .location import search_locations, selected_location, remember_selection, timezone_for, LocationError

PRESETS={'信河街':(120.655,28.018,'Asia/Shanghai'),'鹿城区':(120.655,28.015,'Asia/Shanghai'),'鹿城':(120.655,28.015,'Asia/Shanghai'),'杭州市':(120.1551,30.2741,'Asia/Shanghai'),'杭州':(120.1551,30.2741,'Asia/Shanghai'),'温州市':(120.6994,27.9943,'Asia/Shanghai'),'温州':(120.6994,27.9943,'Asia/Shanghai'),'建德市':(119.2812,29.4747,'Asia/Shanghai'),'台中市':(120.6736,24.1477,'Asia/Taipei'),'东京':(139.6917,35.6895,'Asia/Tokyo')}

class InputError(ValueError):
    pass

def _query(location):
    return ' '.join(str(location.get(k, '')).strip() for k in ('district','city','province','country') if str(location.get(k, '')).strip()).strip()

def resolve_location(location):
    if location.get('longitude') is not None and location.get('latitude') is not None:
        lon, lat = float(location['longitude']), float(location['latitude'])
        tz = str(location.get('iana_timezone') or '').strip() or timezone_for(lon, lat)
        return {'longitude': lon, 'latitude': lat, 'iana_timezone': tz, 'source': 'provided'}
    if location.get('selected'):
        s = dict(location['selected'])
        required = ('longitude','latitude','iana_timezone')
        if all(k in s for k in required):
            remember_selection(_query(location), s)
            s['source'] = 'selected_global_location'
            return s
    q = _query(location)
    if not q:
        raise InputError('请输入出生地点。')
    for name,(lon,lat,tz) in PRESETS.items():
        if name in q:
            return {'longitude':lon,'latitude':lat,'iana_timezone':tz,'source':'offline_fallback'}
    cached = selected_location(q)
    if cached:
        out = dict(cached); out['source'] = 'selected_location_cache'; return out
    rows = search_locations(q, 5)
    if len(rows) == 1:
        remember_selection(q, rows[0]); return rows[0]
    raise InputError('LOCATION_AMBIGUOUS|' + json_compact(rows))

def json_compact(value):
    import json
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

def validate_payload(p):
    b = p.get('birth') or {}
    required = ['year','month','day','hour','minute','gender']
    miss = [k for k in required if k not in b]
    if miss: raise InputError('出生信息不完整：' + ','.join(miss))
    if b['gender'] not in ('male','female'): raise InputError('性别参数无效')
    try: datetime(int(b['year']),int(b['month']),int(b['day']),int(b['hour']),int(b['minute']))
    except Exception as exc: raise InputError('出生日期或时间无效') from exc

def calculate_product(payload):
    validate_payload(payload)
    b = payload['birth']
    try:
        geo = resolve_location(payload.get('location') or {})
    except LocationError as exc:
        raise InputError(str(exc)) from exc
    try: ZoneInfo(geo['iana_timezone'])
    except ZoneInfoNotFoundError as exc: raise InputError('IANA 时区无效：' + str(geo['iana_timezone'])) from exc
    dt = datetime(int(b['year']),int(b['month']),int(b['day']),int(b['hour']),int(b['minute']))
    target = (payload.get('options') or {}).get('target_year')
    out = calculate_full(dt, geo['longitude'], geo['iana_timezone'], b['gender'], target)
    out['geo'] = geo
    out['engine']['version'] = '5.8-COSMIC-WEB'
    out['engine']['yongshen_rule_set'] = 'YONGSHEN_FUSION_V2'
    out['engine']['geo_time_rule'] = 'longitude + IANA timezone + true solar time'
    out['geo']['used_for_calculation'] = True
    out['engine']['product_layer'] = 'COSMIC_REFERENCE_UI_SINGLE_PAGE'
    out['profile'] = {'gender': b['gender'], 'birth_local': dt.strftime('%Y-%m-%d %H:%M')} 
    return out
