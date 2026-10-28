from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .engine import STEMS, BRANCHES
from .casting import JIE, solar_term_utc, sexagenary

YANG_STEMS={'甲','丙','戊','庚','壬'}

def dayun_direction(year_stem:str, gender:str)->str:
    male=gender.lower() in {'male','m','男'}
    yang=year_stem in YANG_STEMS
    return 'forward' if (yang and male) or ((not yang) and (not male)) else 'reverse'

def build_dayun(local_birth:datetime, timezone_name:str, month_pillar_text:str, year_stem:str, gender:str, count:int=10):
    tz=ZoneInfo(timezone_name)
    birth=local_birth.replace(tzinfo=tz) if local_birth.tzinfo is None else local_birth.astimezone(tz)
    direction=dayun_direction(year_stem,gender)
    jie=[]
    for y in (birth.year-1,birth.year,birth.year+1):
        for name,target,_ in JIE:
            jie.append((solar_term_utc(y,name,target).astimezone(tz),name))
    jie.sort()
    target=min(x for x in jie if x[0]>birth) if direction=='forward' else max(x for x in jie if x[0]<birth)
    delta=(target[0]-birth) if direction=='forward' else (birth-target[0])
    days=delta.total_seconds()/86400
    start_age=days/3.0
    # 1 traditional year ~= 365.2422 civil days for date projection
    start_date=birth + timedelta(days=start_age*365.2422)
    stem,branch=month_pillar_text[0],month_pillar_text[1]
    # locate pillar in 60-cycle
    idx=next(i for i in range(60) if STEMS[i%10]==stem and BRANCHES[i%12]==branch)
    step=1 if direction=='forward' else -1
    cycles=[]
    def add_years(dt, years):
        try:
            return dt.replace(year=dt.year+years)
        except ValueError:
            return dt.replace(month=2, day=28, year=dt.year+years)
    for n in range(1,count+1):
        p=sexagenary(idx+step*n)
        s=add_years(start_date,(n-1)*10)
        next_s=add_years(start_date,n*10)
        e=next_s-timedelta(days=1)
        cycles.append({'index':n,'pillar':p.text,'start_age':round(start_age+(n-1)*10,3),'end_age':round(start_age+n*10,3),'start_date':s.date().isoformat(),'end_date':e.date().isoformat()})
    return {'direction':direction,'target_jie':target[1],'target_jie_time':target[0].isoformat(),'days_to_jie':round(days,5),'start_age_decimal':round(start_age,5),'start_date':start_date.date().isoformat(),'cycles':cycles}
