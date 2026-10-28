from __future__ import annotations
from datetime import datetime, timedelta, timezone, date
from math import sin, radians
from zoneinfo import ZoneInfo
from .engine import STEMS, BRANCHES, Pillar, true_solar_time, ambiguous_hour, calculate_from_pillars

JIE = [('小寒',285,'丑'),('立春',315,'寅'),('惊蛰',345,'卯'),('清明',15,'辰'),('立夏',45,'巳'),('芒种',75,'午'),('小暑',105,'未'),('立秋',135,'申'),('白露',165,'酉'),('寒露',195,'戌'),('立冬',225,'亥'),('大雪',255,'子')]
ALL_TERMS = [('小寒',285),('大寒',300),('立春',315),('雨水',330),('惊蛰',345),('春分',0),('清明',15),('谷雨',30),('立夏',45),('小满',60),('芒种',75),('夏至',90),('小暑',105),('大暑',120),('立秋',135),('处暑',150),('白露',165),('秋分',180),('寒露',195),('霜降',210),('立冬',225),('小雪',240),('大雪',255),('冬至',270)]
APPROX = {'小寒':(1,5),'大寒':(1,20),'立春':(2,4),'雨水':(2,19),'惊蛰':(3,5),'春分':(3,20),'清明':(4,4),'谷雨':(4,20),'立夏':(5,5),'小满':(5,21),'芒种':(6,5),'夏至':(6,21),'小暑':(7,7),'大暑':(7,22),'立秋':(8,7),'处暑':(8,23),'白露':(9,7),'秋分':(9,23),'寒露':(10,8),'霜降':(10,23),'立冬':(11,7),'小雪':(11,22),'大雪':(12,7),'冬至':(12,21)}

def _jd(dt: datetime) -> float:
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()/86400 + 2440587.5

def solar_longitude(dt_utc: datetime) -> float:
    """Low-order apparent solar longitude; adequate for MVP boundary finding, not an ephemeris replacement."""
    T=(_jd(dt_utc)-2451545.0)/36525
    L0=(280.46646 + 36000.76983*T + 0.0003032*T*T)%360
    M=radians((357.52911 + 35999.05029*T - 0.0001537*T*T)%360)
    C=(1.914602-0.004817*T-0.000014*T*T)*sin(M)+(0.019993-0.000101*T)*sin(2*M)+0.000289*sin(3*M)
    omega=radians(125.04-1934.136*T)
    return (L0+C-0.00569-0.00478*sin(omega))%360

def _angle_diff(a,b): return ((a-b+180)%360)-180

def solar_term_utc(year:int, name:str, target:float) -> datetime:
    m,d=APPROX[name]
    lo=datetime(year,m,d,tzinfo=timezone.utc)-timedelta(days=2)
    hi=datetime(year,m,d,tzinfo=timezone.utc)+timedelta(days=2)
    # unwrap locally around target and bisect monotonic crossing
    for _ in range(50):
        mid=lo+(hi-lo)/2
        if _angle_diff(solar_longitude(mid),target) < 0: lo=mid
        else: hi=mid
    return lo+(hi-lo)/2

def terms_around(year:int, tz:ZoneInfo):
    rows=[]
    for y in (year-1,year,year+1):
        for name,target in ALL_TERMS:
            rows.append((name, solar_term_utc(y,name,target).astimezone(tz)))
    return sorted(rows,key=lambda x:x[1])

def sexagenary(index:int)->Pillar:
    i=index%60
    return Pillar(STEMS[i%10],BRANCHES[i%12])

def year_pillar(effective_dt:datetime, lichun:datetime)->Pillar:
    y=effective_dt.year if effective_dt>=lichun else effective_dt.year-1
    # 1984 is 甲子 year
    return sexagenary(y-1984)

def month_pillar(effective_dt:datetime, yp:Pillar, tz:ZoneInfo):
    jie=[]
    for y in (effective_dt.year-1,effective_dt.year,effective_dt.year+1):
        for name,target,branch in JIE:
            jie.append((solar_term_utc(y,name,target).astimezone(tz),name,branch))
    jie.sort()
    prev=max(x for x in jie if x[0] <= effective_dt)
    branch=prev[2]; branch_idx=BRANCHES.index(branch)
    # 寅月起干：甲己丙、乙庚戊、丙辛庚、丁壬壬、戊癸甲
    start_map={0:2,5:2,1:4,6:4,2:6,7:6,3:8,8:8,4:0,9:0}
    offset=(branch_idx-BRANCHES.index('寅'))%12
    stem=STEMS[(start_map[STEMS.index(yp.stem)]+offset)%10]
    return Pillar(stem,branch), {'previous_jie':prev[1],'previous_jie_time':prev[0].isoformat()}

def day_pillar(true_dt:datetime)->Pillar:
    # User-selected rule: 23:00 changes to the next BaZi day. 2000-01-07 is verified 甲子.
    d=true_dt.date() + (timedelta(days=1) if true_dt.hour>=23 else timedelta())
    ref=date(2000,1,7)
    return sexagenary((d-ref).days)

def hour_pillar(true_dt:datetime, dp:Pillar)->Pillar:
    bi=((true_dt.hour+1)//2)%12
    # 子时起干：甲己甲、乙庚丙、丙辛戊、丁壬庚、戊癸壬
    ds=STEMS.index(dp.stem)
    start={0:0,5:0,1:2,6:2,2:4,7:4,3:6,8:6,4:8,9:8}[ds]
    return Pillar(STEMS[(start+bi)%10],BRANCHES[bi])

def cast_birth(local_dt:datetime, longitude:float, iana_timezone:str, gender:str='unknown') -> dict:
    tz=ZoneInfo(iana_timezone)
    aware=local_dt.replace(tzinfo=tz) if local_dt.tzinfo is None else local_dt.astimezone(tz)
    dst_min=int((aware.dst() or timedelta()).total_seconds()/60)
    standard_naive=aware.replace(tzinfo=None)-timedelta(minutes=dst_min)
    standard_offset=((aware.utcoffset() or timedelta()).total_seconds()/3600) - dst_min/60
    solar=true_solar_time(standard_naive,longitude,standard_offset)
    true_dt=datetime.fromisoformat(solar['true_solar_datetime'])
    # attach standard timezone solely for comparison with term instants
    true_aware=true_dt.replace(tzinfo=tz)
    lichun=solar_term_utc(true_dt.year,'立春',315).astimezone(tz)
    yp=year_pillar(true_aware,lichun)
    mp,term_meta=month_pillar(true_aware,yp,tz)
    dp=day_pillar(true_dt)
    hp=hour_pillar(true_dt,dp)
    core=calculate_from_pillars([yp,mp,dp,hp])
    amb=ambiguous_hour(true_dt)
    nearest_terms=terms_around(true_dt.year,tz)
    prev=max((x for x in nearest_terms if x[1]<=true_aware), key=lambda x:x[1]); nxt=min((x for x in nearest_terms if x[1]>true_aware), key=lambda x:x[1])
    dist=min(abs((true_aware-prev[1]).total_seconds()),abs((nxt[1]-true_aware).total_seconds()))/60
    return {
      'engine':{'version':'2.2.0','rule_set':'YONGSHEN_CORE_V1'},
      'birth':{'local_datetime':aware.isoformat(),'gender':gender,'longitude':longitude,'iana_timezone':iana_timezone},
      'time_correction':{**solar,'dst_detected':bool(dst_min),'dst_offset_minutes':dst_min,'standard_utc_offset_hours':standard_offset},
      'solar_terms':{**term_meta,'lichun_time':lichun.isoformat(),'next_term':nxt[0],'next_term_time':nxt[1].isoformat(),'ambiguous_solar_term_flag':dist<=10,'nearest_term_distance_minutes':round(dist,2)},
      **core,
      'warnings':(['AMBIGUOUS_HOUR'] if amb['ambiguous_time_flag'] else []) + (['SOLAR_TERM_BOUNDARY'] if dist<=10 else []),
      'boundary':amb
    }
