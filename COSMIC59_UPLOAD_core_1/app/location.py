from __future__ import annotations
from pathlib import Path
import json
import urllib.parse
import urllib.request

CACHE_FILE = Path(__file__).resolve().parent.parent / 'geo_cache.json'
USER_AGENT = 'BaZi-YongShen-Global/4.1 (local desktop application)'

class LocationError(ValueError):
    pass

def _cache_load():
    try:
        return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}

def _cache_save(data):
    try:
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass

def timezone_for(lon, lat, country_code=''):
    """Resolve IANA timezone without a large local polygon dependency.

    Uses a lightweight coordinate web service, then safe single-zone country/region
    fallbacks. The selected IANA id is cached with the geocoding result.
    """
    country_code = (country_code or '').upper()
    safe = {
        'CN':'Asia/Shanghai','TW':'Asia/Taipei','HK':'Asia/Hong_Kong','MO':'Asia/Macau',
        'JP':'Asia/Tokyo','KR':'Asia/Seoul','SG':'Asia/Singapore','IS':'Atlantic/Reykjavik'
    }
    params = urllib.parse.urlencode({'latitude': float(lat), 'longitude': float(lon)})
    url = 'https://timeapi.io/api/timezone/coordinate?' + params
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        tz = data.get('timeZone') or data.get('timezone') or data.get('timeZoneId')
        if tz and isinstance(tz, str) and '/' in tz:
            return tz
    except Exception:
        pass
    if country_code in safe:
        return safe[country_code]
    raise LocationError('已找到地点，但时区服务暂时无法连接。请稍后重试，或在高级位置填写 IANA 时区。')

def _normalize(row):
    lon, lat = float(row['lon']), float(row['lat'])
    address = row.get('address') or {}
    return {
        'place_id': str(row.get('place_id', '')),
        'display_name': row.get('display_name') or '',
        'longitude': lon,
        'latitude': lat,
        'iana_timezone': timezone_for(lon, lat, address.get('country_code', '')),
        'country_code': address.get('country_code', '').upper(),
        'type': row.get('type') or row.get('addresstype') or '',
        'source': 'global_geocoder'
    }

def search_locations(query, limit=5):
    query = (query or '').strip()
    if not query:
        raise LocationError('请输入出生地点。')
    limit = max(1, min(int(limit or 5), 8))
    cache = _cache_load()
    ckey = 'search:' + query.lower()
    cached = cache.get(ckey)
    if isinstance(cached, list) and cached:
        return cached[:limit]
    params = {
        'q': query, 'format': 'jsonv2', 'limit': limit,
        'addressdetails': 1, 'accept-language': 'zh-CN,zh-TW,zh,en'
    }
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            rows = json.loads(resp.read().decode('utf-8'))
    except Exception as exc:
        raise LocationError('全球地点服务暂时无法连接。请检查网络，或使用高级位置填写经纬度和 IANA 时区。') from exc
    if not rows:
        raise LocationError('没有找到这个地点。请增加国家、省州、城市或区县信息后重试。')
    results = []
    for row in rows:
        try:
            results.append(_normalize(row))
        except LocationError:
            continue
    if not results:
        raise LocationError('找到地点，但无法确定其时区。请使用高级位置填写经纬度和 IANA 时区。')
    cache[ckey] = results
    _cache_save(cache)
    return results[:limit]

def remember_selection(query, result):
    query = (query or '').strip()
    if not query:
        return
    cache = _cache_load()
    cache['selected:' + query.lower()] = result
    _cache_save(cache)

def selected_location(query):
    query = (query or '').strip()
    if not query:
        return None
    value = _cache_load().get('selected:' + query.lower())
    return value if isinstance(value, dict) else None
