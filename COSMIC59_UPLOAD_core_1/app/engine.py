from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from math import pi, sin, cos
from typing import Dict, List, Optional

STEMS = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
STEM_ELEMENT = dict(zip(STEMS, ['木','木','火','火','土','土','金','金','水','水']))
STEM_YY = dict(zip(STEMS, ['阳','阴','阳','阴','阳','阴','阳','阴','阳','阴']))
HIDDEN = {
 '子': {'癸':1.0}, '丑': {'己':.6,'癸':.3,'辛':.1}, '寅': {'甲':.6,'丙':.3,'戊':.1},
 '卯': {'乙':1.0}, '辰': {'戊':.6,'乙':.3,'癸':.1}, '巳': {'丙':.6,'戊':.3,'庚':.1},
 '午': {'丁':.7,'己':.3}, '未': {'己':.6,'丁':.3,'乙':.1}, '申': {'庚':.6,'壬':.3,'戊':.1},
 '酉': {'辛':1.0}, '戌': {'戊':.6,'辛':.3,'丁':.1}, '亥': {'壬':.7,'甲':.3}
}
STATE_COEF = {'旺':2.0,'相':1.414,'休':1.0,'囚':.707,'死':.5}
SEASON_STATE = {
 '寅': {'木':'旺','火':'相','水':'休','金':'囚','土':'死'}, '卯': {'木':'旺','火':'相','水':'休','金':'囚','土':'死'},
 '巳': {'火':'旺','土':'相','木':'休','水':'囚','金':'死'}, '午': {'火':'旺','土':'相','木':'休','水':'囚','金':'死'},
 '申': {'金':'旺','水':'相','土':'休','火':'囚','木':'死'}, '酉': {'金':'旺','水':'相','土':'休','火':'囚','木':'死'},
 '亥': {'水':'旺','木':'相','金':'休','土':'囚','火':'死'}, '子': {'水':'旺','木':'相','金':'休','土':'囚','火':'死'},
 # 四季土月：V2.1 暂用土旺近似，后续由逐日司令表覆盖
 '辰': {'土':'旺','金':'相','火':'休','木':'囚','水':'死'}, '戌': {'土':'旺','金':'相','火':'休','木':'囚','水':'死'},
 '丑': {'土':'旺','金':'相','火':'休','木':'囚','水':'死'}, '未': {'土':'旺','金':'相','火':'休','木':'囚','水':'死'},
}
GENERATES = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
CONTROLS = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
GENERATED_BY = {v:k for k,v in GENERATES.items()}
CONTROLLED_BY = {v:k for k,v in CONTROLS.items()}

@dataclass
class Pillar:
    stem: str
    branch: str
    @property
    def text(self): return self.stem + self.branch


def equation_of_time_minutes(dt: datetime) -> float:
    n = dt.timetuple().tm_yday
    days = 366 if (dt.year % 4 == 0 and (dt.year % 100 != 0 or dt.year % 400 == 0)) else 365
    gamma = 2*pi/days * (n-1 + (dt.hour + dt.minute/60 - 12)/24)
    return 229.18*(0.000075 + 0.001868*cos(gamma) - 0.032077*sin(gamma) - 0.014615*cos(2*gamma) - 0.040849*sin(2*gamma))


def true_solar_time(civil_standard_dt: datetime, longitude: float, standard_utc_offset_hours: float) -> dict:
    meridian = 15 * standard_utc_offset_hours
    longitude_correction = 4 * (longitude - meridian)
    eot = equation_of_time_minutes(civil_standard_dt)
    total = longitude_correction + eot
    return {
        'standard_datetime': civil_standard_dt.isoformat(),
        'timezone_meridian': meridian,
        'longitude_correction_minutes': round(longitude_correction, 3),
        'equation_of_time_minutes': round(eot, 3),
        'total_correction_minutes': round(total, 3),
        'true_solar_datetime': (civil_standard_dt + timedelta(minutes=total)).isoformat()
    }


def ambiguous_hour(dt: datetime, threshold=8) -> dict:
    minute_of_day = dt.hour*60 + dt.minute + dt.second/60
    bounds = [60,180,300,420,540,660,780,900,1020,1140,1260,1380]
    # 23:00 boundary also acts across midnight
    candidates = bounds + [-60, 1500]
    nearest = min(candidates, key=lambda x: abs(minute_of_day-x))
    distance = abs(minute_of_day-nearest)
    return {'ambiguous_time_flag': distance <= threshold, 'distance_minutes': round(distance,2)}


def element_initial(pillars: List[Pillar]) -> Dict[str,float]:
    out = {e:0.0 for e in '木火土金水'}
    for p in pillars:
        out[STEM_ELEMENT[p.stem]] += 100
        for hs, ratio in HIDDEN[p.branch].items():
            out[STEM_ELEMENT[hs]] += 100*ratio
    return out


def element_strength(pillars: List[Pillar]) -> Dict[str,dict]:
    initial = element_initial(pillars)
    month_branch = pillars[1].branch
    states = SEASON_STATE[month_branch]
    result = {}
    for e,val in initial.items():
        state = states[e]
        coef = STATE_COEF[state]
        result[e] = {'initial_value':round(val,3),'state':state,'state_coefficient':coef,'final_value':round(val*coef,3)}
    return result


def root_strength(day_stem: str, pillars: List[Pillar]) -> dict:
    dm = STEM_ELEMENT[day_stem]
    pos = {'year':.45,'month':1.0,'day':.85,'hour':.55}
    labels = ['year','month','day','hour']
    total=0.0; roots=[]
    for label,p in zip(labels,pillars):
        same = [(hs,r) for hs,r in HIDDEN[p.branch].items() if STEM_ELEMENT[hs] == dm]
        for hs,r in same:
            score = pos[label]*r
            total += score
            roots.append({'position':label,'branch':p.branch,'hidden_stem':hs,'score':round(score,3)})
    level = '无根' if total == 0 else '微根' if total < .3 else '弱根' if total < .7 else '中根' if total <= 1.3 else '强根'
    return {'root': total>0, 'root_strength':round(total,3),'root_level':level,'details':roots}


def classify_and_yongshen(pillars: List[Pillar], strengths: Dict[str,dict]) -> dict:
    """Rule-fusion resolver.

    Important: this does NOT select the lowest-count element.  It first checks
    structure/root/cong, then combines climate (调候), support/control (扶抑),
    passage (通关), excess-remedy (病药) and the downstream generate/control
    consequences of adding each candidate element.
    """
    dm = STEM_ELEMENT[pillars[2].stem]
    resource = GENERATED_BY[dm]
    output = GENERATES[dm]
    wealth = CONTROLS[dm]
    officer = CONTROLLED_BY[dm]
    vals = {e:v['final_value'] for e,v in strengths.items()}
    total = sum(vals.values()) or 1.0
    support = vals[dm] + vals[resource]
    opposition = vals[output] + vals[wealth] + vals[officer]
    ratio = support/(support+opposition) if support+opposition else .5
    roots = root_strength(pillars[2].stem,pillars)
    max_element=max(vals,key=vals.get); dominance=vals[max_element]/total

    # 从格必须先判。这里采用严格候选门槛；有明显根气时不按“弱就从”。
    cong = roots['root_strength'] <= .15 and dominance >= .82
    if cong: strength_class='从格候选'
    elif ratio >= .58: strength_class='身强'
    elif ratio < .45: strength_class='身弱'
    else: strength_class='中和区'

    scores={e:0.0 for e in vals}
    reasons={e:[] for e in vals}
    trace=[]
    def add(e, score, why, method):
        scores[e]+=score; reasons[e].append(f'{method}：{why}')
        trace.append({'method':method,'element':e,'score':round(score,2),'reason':why})

    month=pillars[1].branch
    # 1 调候：优先级最高。这里按既定产品规则，不以“缺某元素”为触发条件。
    if month in ['亥','子','丑']:
        add('火',48,'冬令寒湿，先取火暖局','调候')
        add('土',24,'火暖后以土承载、制约寒湿水势','调候')
        add('金',8,'作为后续结构辅助，不越过火土优先级','调候')
    elif month in ['巳','午','未']:
        add('水',48,'夏令燥热，先取水润燥降温','调候')
        add('金',22,'金可生水并辅助调候','调候')

    # 2 扶抑：从格时不反向硬扶。
    if not cong:
        if strength_class=='身强':
            for e,s0,why in [(output,31,'泄日主'),(wealth,29,'耗日主'),(officer,27,'制日主')]: add(e,s0,why,'扶抑')
        elif strength_class=='身弱':
            add(resource,36,'印星生扶日主','扶抑'); add(dm,30,'比劫直接扶身','扶抑')
        else:
            add(resource,12,'中和区小幅取生扶以保持承载力','扶抑')
    else:
        add(max_element,38,'严格从势候选，顺主导旺势','从格')
        add(GENERATES[max_element],16,'顺势泄秀','从格')

    # 3 通关：两股相克力量都明显时，引入中介元素。
    passage_pairs=[('金','木','水'),('水','火','木'),('火','金','土'),('土','水','金'),('木','土','火')]
    avg=total/5
    for a,b,bridge in passage_pairs:
        if vals[a] >= avg*.9 and vals[b] >= avg*.9:
            add(bridge,18,f'{a}{b}两势并见，以{bridge}作通关候选','通关')

    # 4 病药：针对明显过旺者，不是“谁最少补谁”。
    for e,v in vals.items():
        if v > avg*1.60:
            scores[e]-=26; reasons[e].append('病药：本气偏旺，降低继续增加的优先级')
            trace.append({'method':'病药','element':e,'score':-26,'reason':'本气明显偏旺，避免继续堆叠'})
            drug=CONTROLLED_BY[e]
            add(drug,20,f'制约偏旺的{e}','病药')

    # 5 生克链净效应：评价“加进去之后生谁、克谁、又把能量导向哪里”。
    # 身弱时，候选若直接生扶日主加分；若继续生旺主要压力源则降分。
    pressure=max((output,wealth,officer), key=lambda e: vals[e])
    for e in vals:
        net=0.0; notes=[]
        if GENERATES[e] == dm: net+=12; notes.append('可生扶日主')
        if e == dm: net+=8; notes.append('直接扶身')
        if CONTROLS[e] == pressure: net+=9; notes.append(f'可制主要压力源{pressure}')
        if GENERATES[e] == pressure: net-=10; notes.append(f'会继续生旺主要压力源{pressure}')
        if e == pressure: net-=8; notes.append(f'直接增加主要压力源{pressure}')
        # 对身强反向处理：更重视泄耗制，而不是继续生扶。
        if strength_class=='身强':
            if GENERATES[e] == dm: net-=10
            if e == dm: net-=8
            if e in (output,wealth,officer): net+=8
        if cong:
            net=0.0  # 从格路径不使用普通身强身弱的链式修正
        if net:
            add(e,net,'；'.join(notes),'生克链')

    # 候选不能因为自身数值最低自动获奖；仅作轻微饱和惩罚，防止过量继续堆叠。
    for e,v in vals.items():
        saturation=max(0.0,(v/total)-.30)*35
        if saturation:
            scores[e]-=saturation
            reasons[e].append(f'饱和度：现有占比偏高，扣减{round(saturation,1)}')

    ranked=sorted(scores,key=lambda e:(scores[e],-vals[e]),reverse=True)
    # 忌神优先从“低净效应 + 原局已有压力”中取，不再简单取最低计分的孤立元素。
    ji_candidates=sorted(vals,key=lambda e:(scores[e],-vals[e]))
    ji=ji_candidates[0]
    return {
      'day_master': {'element':dm, **roots,'support_strength':round(support,3),'opposition_strength':round(opposition,3),'strength_ratio':round(ratio,4),'strength_class':strength_class},
      'pattern': {'cong_ge_checked':True,'cong_ge_triggered':cong,'dominance_ratio':round(dominance,4),'dominant_element':max_element},
      'yong_shen': {'first':ranked[0],'second':ranked[1],'third':ranked[2],'ji_shen':[ji],
                    'scores':{e:round(scores[e],2) for e in scores},'reasons':reasons,
                    'decision_trace':trace,'selection_principle':'从格先判 → 调候 → 扶抑 → 通关 → 病药 → 生克链净效应；不采用缺什么补什么'},
      'analysis_meta': {'month_branch':month,'pressure_element':pressure,'average_strength':round(avg,3)}
    }

MAPPING={
 '火': {'colors':['红','紫','橙'],'materials':['红绳','化纤绳','朱砂','红玛瑙'],'directions':['南']},
 '土': {'colors':['黄','棕','米'],'materials':['陶瓷','黄晶','虎眼石','蜜蜡'],'directions':['中央','西南','东北']},
 '金': {'colors':['白','金','银'],'materials':['金','银','白水晶'],'directions':['西','西北']},
 '水': {'colors':['黑','蓝','灰'],'materials':['黑曜石','海蓝宝'],'directions':['北']},
 '木': {'colors':['绿','青','翠'],'materials':['木质','绿松石'],'directions':['东','东南']},
}
# Product roles are deliberately separated. An element does not reuse the same
# material wording when it is a cord versus a bead.
CORD_MAPPING={
 '火': {'colors':['正红','朱红','酒红'],'materials':['红色编织绳','朱红色丝绳']},
 '土': {'colors':['棕黄','卡其','米棕'],'materials':['棕黄色编织绳','卡其色丝绳']},
 '金': {'colors':['米白','银灰','香槟金'],'materials':['米白色编织绳','银灰色丝绳']},
 '水': {'colors':['藏蓝','黑','深灰'],'materials':['藏蓝色编织绳','黑色编织绳']},
 '木': {'colors':['墨绿','青绿','翠绿'],'materials':['墨绿色编织绳','青绿色丝绳']},
}
BEAD_MAPPING={
 '火': {'colors':['红','紫红','橙红'],'materials':['南红玛瑙','红玛瑙','石榴石']},
 '土': {'colors':['黄','棕','蜜色'],'materials':['虎眼石','黄水晶','蜜蜡','土系陶瓷珠']},
 '金': {'colors':['白','银','金'],'materials':['白水晶','银饰珠','金属隔珠']},
 '水': {'colors':['黑','蓝','灰'],'materials':['黑曜石','海蓝宝','青金石']},
 '木': {'colors':['绿','青','木色'],'materials':['绿松石','檀木珠','沉香木珠']},
}

def _role_piece(element, role):
    base=MAPPING[element]
    rolemap=CORD_MAPPING[element] if role=='cord' else BEAD_MAPPING[element]
    return {'element':element,'colors':rolemap['colors'],'materials':rolemap['materials'],'directions':base['directions'],'role':role}

def map_output(y:dict)->dict:
    a,b,c=y['first'],y['second'],y['third']; ji=y['ji_shen'][0]
    return {'main_cord':_role_piece(a,'cord'),'primary_bead':_role_piece(b,'primary_bead'),'secondary_bead':_role_piece(c,'secondary_bead'),'avoid_beads':{'element':ji,**MAPPING[ji]},'wear_hand':'左手','mapping_version':'ROLE_SEPARATED_V1'}


def calculate_from_pillars(pillars: List[Pillar]) -> dict:
    strengths=element_strength(pillars)
    decision=classify_and_yongshen(pillars,strengths)
    return {'four_pillars':{k:asdict(v)|{'text':v.text} for k,v in zip(['year','month','day','hour'],pillars)},'element_strength':strengths,**decision,'mapping':map_output(decision['yong_shen'])}
