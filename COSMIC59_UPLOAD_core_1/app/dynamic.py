from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
from .engine import _role_piece, STEMS, BRANCHES, STEM_ELEMENT, HIDDEN, MAPPING, GENERATES
from .casting import sexagenary, solar_term_utc

STEM_COMBINES={frozenset(x):v for x,v in [(('甲','己'),'土'),(('乙','庚'),'金'),(('丙','辛'),'水'),(('丁','壬'),'木'),(('戊','癸'),'火')]}
BRANCH_COMBINES={frozenset(x):v for x,v in [(('子','丑'),'土'),(('寅','亥'),'木'),(('卯','戌'),'火'),(('辰','酉'),'金'),(('巳','申'),'水'),(('午','未'),'土')]}
CLASHES={frozenset(x) for x in [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]}
HARMS={frozenset(x) for x in [('子','未'),('丑','午'),('寅','巳'),('卯','辰'),('申','亥'),('酉','戌')]}
BREAKS={frozenset(x) for x in [('子','酉'),('丑','辰'),('寅','亥'),('卯','午'),('巳','申'),('未','戌')]}
THREE_HARMONIES={frozenset(x):v for x,v in [(('申','子','辰'),'水'),(('亥','卯','未'),'木'),(('寅','午','戌'),'火'),(('巳','酉','丑'),'金')]}
THREE_MEETINGS={frozenset(x):v for x,v in [(('寅','卯','辰'),'木'),(('巳','午','未'),'火'),(('申','酉','戌'),'金'),(('亥','子','丑'),'水')]}
THREE_PUNISHMENTS=[frozenset(('寅','巳','申')),frozenset(('丑','戌','未'))]
SELF_PUNISH=set('辰午酉亥')

def pillar_supply(text:str)->dict:
    out={e:0.0 for e in '木火土金水'}
    out[STEM_ELEMENT[text[0]]]+=100
    for s,r in HIDDEN[text[1]].items(): out[STEM_ELEMENT[s]]+=100*r
    return out

def interaction_scan(natal:list[str], dayun:str, liunian:str)->list[dict]:
    rows=[]
    sources=[('大运',dayun),('流年',liunian)]
    targets=[('年柱',natal[0]),('月柱',natal[1]),('日柱',natal[2]),('时柱',natal[3]),('大运',dayun)]
    for sn,sp in sources:
        for tn,tp in targets:
            if sn==tn: continue
            sk=frozenset((sp[0],tp[0])); bk=frozenset((sp[1],tp[1]))
            if sk in STEM_COMBINES: rows.append({'type':'天干合','source':sn,'target':tn,'pair':sp[0]+tp[0],'transform_tendency':STEM_COMBINES[sk]})
            if bk in BRANCH_COMBINES: rows.append({'type':'六合','source':sn,'target':tn,'pair':sp[1]+tp[1],'transform_tendency':BRANCH_COMBINES[bk]})
            if bk in CLASHES: rows.append({'type':'六冲','source':sn,'target':tn,'pair':sp[1]+tp[1]})
            if bk in HARMS: rows.append({'type':'六害','source':sn,'target':tn,'pair':sp[1]+tp[1]})
            if bk in BREAKS: rows.append({'type':'六破','source':sn,'target':tn,'pair':sp[1]+tp[1]})
            if sp[1]==tp[1] and sp[1] in SELF_PUNISH: rows.append({'type':'自刑','source':sn,'target':tn,'pair':sp[1]*2})
    branches=[x[1] for x in natal]+[dayun[1],liunian[1]]
    bs=set(branches)
    for group,e in THREE_HARMONIES.items():
        if group<=bs: rows.append({'type':'三合','branches':''.join(sorted(group)),'element':e})
    for group,e in THREE_MEETINGS.items():
        if group<=bs: rows.append({'type':'三会','branches':''.join(sorted(group)),'element':e})
    for group in THREE_PUNISHMENTS:
        if group<=bs: rows.append({'type':'三刑','branches':''.join(sorted(group))})
    if {'子','卯'}<=bs: rows.append({'type':'子卯刑','branches':'子卯'})
    return rows

def annual_pillar(year:int, tz_name='Asia/Shanghai', month=7, day=1)->str:
    # Annual analysis uses the BaZi solar year: after LiChun -> current Gregorian year pillar.
    # For whole-year labels we return the pillar governing the majority of that Gregorian year.
    return sexagenary(year-1984).text

def active_dayun(dayun:dict, target_year:int):
    # Annual view uses July 1 as the representative date so a late-year handover
    # is not incorrectly shown as active for the whole Gregorian year.
    probe = datetime(target_year, 7, 1).date()
    for c in dayun.get('cycles', []):
        start = datetime.fromisoformat(c['start_date']).date()
        end = datetime.fromisoformat(c['end_date']).date()
        if start <= probe < end:
            return c
    return None

def dynamic_analysis(chart:dict, dayun:dict, target_year:int)->dict:
    natal=[chart['four_pillars'][k]['text'] for k in ['year','month','day','hour']]
    active=active_dayun(dayun,target_year)
    if not active: raise ValueError('target year outside generated DaYun range')
    ly=annual_pillar(target_year)
    ds=pillar_supply(active['pillar']); ys=pillar_supply(ly)
    natal_vals={e:v['final_value'] for e,v in chart['element_strength'].items()}
    dynamic={e:round(natal_vals[e]+.45*ds[e]+.25*ys[e],3) for e in natal_vals}
    y=chart['yong_shen']; base_scores=y['scores']; top=[y['first'],y['second'],y['third']]
    # Need is normalized from positive decision score; supply measures dynamic addition relative to one pillar (200 points).
    saturation={}
    for e in top:
        need=max(base_scores[e],1)
        supply=.45*ds[e]+.25*ys[e]
        sat=min(1.5,supply/(need*2.0))
        saturation[e]={'base_need_score':round(need,2),'dynamic_supply':round(supply,2),'saturation':round(sat,3),'remaining_need':round(max(0,need-supply/2),2)}
    activation={}
    for e in y['ji_shen']:
        supply=.45*ds[e]+.25*ys[e]
        interaction_bonus=sum(12 for r in interaction_scan(natal,active['pillar'],ly) if r.get('element')==e)
        score=min(100, supply/1.4+interaction_bonus)
        activation[e]={'score':round(score,2),'level':'HIGH' if score>=65 else 'MEDIUM' if score>=35 else 'LOW'}
    max_ji=max((v['score'] for v in activation.values()),default=0)
    avg_sat=sum(v['saturation'] for v in saturation.values())/len(saturation)
    state='CONSERVATIVE' if max_ji>=65 else 'EXPAND' if avg_sat>=.35 and max_ji<35 else 'BALANCED'
    # annual mapping: rank natal favorable elements by remaining need, never invert natal taboo into a recommendation
    annual_rank=sorted(top,key=lambda e:saturation[e]['remaining_need'],reverse=True)
    annual_mapping={'main_cord':_role_piece(annual_rank[0],'cord'),'primary_bead':_role_piece(annual_rank[1],'primary_bead'),'secondary_bead':_role_piece(annual_rank[2],'secondary_bead'),'avoid_beads':chart['mapping']['avoid_beads'],'wear_hand':'左手','mapping_version':'ROLE_SEPARATED_V1'}
    return {'target_year':target_year,'year_pillar':ly,'active_dayun':active,'dynamic_element_strength':dynamic,'interactions':interaction_scan(natal,active['pillar'],ly),'yong_shen_saturation':saturation,'ji_shen_activation':activation,'dynamic_state':state,'annual_mapping':annual_mapping,'model_weights':{'natal':1.0,'dayun':.45,'liunian':.25}}
