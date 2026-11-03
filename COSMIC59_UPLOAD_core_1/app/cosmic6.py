from __future__ import annotations
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from secrets import randbelow
from typing import Any
import calendar

VERSION = "6.0.0"

def _jsonable(obj: Any, depth: int = 0):
    if depth > 5: return str(obj)
    if obj is None or isinstance(obj, (str, int, float, bool)): return obj
    if isinstance(obj, (list, tuple)): return [_jsonable(x, depth+1) for x in obj]
    if isinstance(obj, dict): return {str(k): _jsonable(v, depth+1) for k,v in obj.items()}
    for method in ("model_dump", "dict"):
        fn = getattr(obj, method, None)
        if callable(fn):
            try: return _jsonable(fn(), depth+1)
            except Exception: pass
    if hasattr(obj, "__dict__"):
        return {k:_jsonable(v,depth+1) for k,v in vars(obj).items() if not k.startswith("_")}
    return str(obj)

def _validate_birth(p):
    b = p.get("birth") or {}
    for k in ("year","month","day","hour","minute","gender"):
        if k not in b: raise ValueError("出生信息缺少字段：" + k)
    dt = datetime(int(b["year"]),int(b["month"]),int(b["day"]),int(b["hour"]),int(b["minute"]))
    if b["gender"] not in ("male","female"): raise ValueError("gender 必须是 male 或 female")
    return dt,b

def ziwei_chart(dt: datetime, gender: str):
    try:
        from iztro_py import by_solar
    except ImportError as exc:
        raise RuntimeError("紫微斗数依赖未安装：请安装 requirements-v6.txt") from exc
    shichen = (dt.hour + 1)//2
    if dt.hour == 23: shichen = 12
    shichen = max(0,min(12,shichen))
    chart = by_solar(f"{dt.year}-{dt.month}-{dt.day}", shichen, "男" if gender=="male" else "女")
    palaces = []
    raw = getattr(chart, "palaces", None)
    if raw is None:
        raw = getattr(chart, "palace_list", None)
    if raw is not None:
        for palace in raw:
            palaces.append(_jsonable(palace))
    stars = {}
    for name in ("紫微","天机","太阳","武曲","天同","廉贞","天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"):
        try:
            star = chart.star(name)
            if star: stars[name] = {"palace": getattr(getattr(star,"palace",lambda:None)(),"name",None),
                                    "brightness": getattr(star,"brightness",None),
                                    "mutagen": getattr(star,"mutagen",None)}
        except Exception: pass
    result = {
        "engine":"iztro-py", "solar_date":str(getattr(chart,"solar_date",dt.date())),
        "lunar_date":str(getattr(chart,"lunar_date","")),
        "zodiac":str(getattr(chart,"zodiac","")), "five_elements_class":str(getattr(chart,"five_elements_class","")),
        "soul_palace":_jsonable(chart.get_soul_palace()),
        "body_palace":_jsonable(chart.get_body_palace()) if hasattr(chart,"get_body_palace") else None,
        "palaces":palaces, "major_stars":stars,
        
        "rule_note":"采用 iztro-py 排盘规则；流派参数应在产品设置中显式选择。"
    }
    return result

def lunar_calendar(dt: datetime):
    try:
        from lunar_python import Solar
    except ImportError as exc:
        raise RuntimeError("农历历法依赖未安装：请安装 requirements-v6.txt") from exc
    solar = Solar.fromYmdHms(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second)
    lunar = solar.getLunar()
    return {"solar":solar.toYmdHms(),"lunar":lunar.toFullString(),
            "year_ganzhi":lunar.getYearInGanZhi(),"month_ganzhi":lunar.getMonthInGanZhi(),
            "day_ganzhi":lunar.getDayInGanZhi(),"time_ganzhi":lunar.getTimeInGanZhi(),
            "jieqi":lunar.getJieQi()}

def analyze(payload):
    dt,b = _validate_birth(payload)
    from app.product import calculate_product
    base_payload = dict(payload)
    base_payload.setdefault("options",{})
    base_payload["options"] = dict(base_payload["options"])
    target_year = int(base_payload["options"].get("target_year") or datetime.now().year)
    base_payload["options"]["target_year"] = target_year
    bazi = calculate_product(base_payload)
    ziwei = ziwei_chart(dt,b["gender"])
    lunar = lunar_calendar(dt)
    return {"version":VERSION,"birth_profile":bazi.get("profile"),"geo":bazi.get("geo"),
            "bazi":bazi,"ziwei":ziwei,"lunar_calendar":lunar,
            "annual":bazi.get("liu_nian"),
            "rule_versions":{"bazi":bazi.get("engine",{}).get("version"),"ziwei":"iztro-py","calendar":"lunar-python"},
            "limitations":["堪舆需要房屋坐向、建成年份及平面资料，未提供时不推断。","易经及灵签必须由用户主动起卦/摇签，不与出生盘混为一谈。"]}

def cast_yijing(payload):
    question = str(payload.get("question","")).strip()
    if not question: raise ValueError("请先填写本次所问事项。")
    # Three-coin method, each toss: 2=yin, 3=yang; totals 6/7/8/9.
    lines=[]
    for _ in range(6):
        toss=[2+randbelow(2) for _ in range(3)]
        total=sum(toss)
        lines.append({"value":total,"line":"yang" if total in (7,9) else "yin",
                      "moving":total in (6,9),"coins":toss})
    bits=[1 if x["line"]=="yang" else 0 for x in lines]
    changed=[(1-v if x["moving"] else v) for v,x in zip(bits,lines)]
    trigram_names={0:"坤",1:"震",2:"坎",3:"兑",4:"艮",5:"离",6:"巽",7:"乾"}
    lower=sum(bits[i]<<i for i in range(3)); upper=sum(bits[i+3]<<(i) for i in range(3))
    lower2=sum(changed[i]<<i for i in range(3)); upper2=sum(changed[i+3]<<(i) for i in range(3))
    return {"method":"三枚铜钱法（模拟投掷）","question":question,"cast_at":datetime.now().astimezone().isoformat(),
            "lines_bottom_to_top":lines,"original_trigrams":{"lower":trigram_names[lower],"upper":trigram_names[upper]},
            "changed_trigrams":{"lower":trigram_names[lower2],"upper":trigram_names[upper2]},
            "moving_lines":[i+1 for i,x in enumerate(lines) if x["moving"]],
            "note":"已生成六爻阴阳及动爻。完整卦名、卦辞、爻辞须由经校验的六十四卦典籍数据表映射，当前不编造原文。"}

def draw_lingqian(payload):
    category=str(payload.get("category","")).strip()
    series=str(payload.get("series","黄大仙灵签")).strip()
    days=int(payload.get("days",7))
    if series!="黄大仙灵签": raise ValueError("当前此接口仅支持黄大仙灵签。")
    if not category: raise ValueError("请选择求签事项类型。")
    if days not in (1,3,7,14,30): raise ValueError("时间范围只支持 1/3/7/14/30 天。")
    number=randbelow(100)+1
    return {"series":series,"category":category,"days":days,"number":number,
            "drawn_at":datetime.now().astimezone().isoformat(),"status":"SIGN_TEXT_DATA_REQUIRED",
            "interpretation":{"plain":"签号已随机抽取。导入经核对的黄大仙一百签原文版本后，系统才会展示签文、白话解、典故及逐日建议。","advice":"把签文作为反思提示，不作为医疗、法律、投资或重大决定的唯一依据。"},
            "source_requirement":"需在 data/huangdaxian_100.json 中配置选定版本的100签原文、签题、典故与等级；不同流传版本不可混用。"}

def fengshui_flying_stars(payload):
    direction=float(payload.get("facing_degrees"))
    if not 0 <= direction < 360: raise ValueError("朝向角度须为 0–359.9 度。")
    year=int(payload.get("target_year") or datetime.now().year)
    built=int(payload.get("built_year") or year)
    period=max(1,min(9,(built-1864)//20+1))
    sectors=["北","西南","东","东南","中","西北","西","东北","南"]
    # Annual flying star center star; Luo Shu flight order from center, NW, W, NE, S, N, SW, E, SE.
    center=((11-(year%9)-1)%9)+1
    flight=[4,9,2,3,5,7,8,1,6] # sector indices for Luo Shu palace arrangement N,SW,E,SE,C,NW,W,NE,S
    stars={}
    for step,sector_index in enumerate(flight):
        stars[sectors[sector_index]]=((center-1-step)%9)+1
    facing_index=int(((direction+22.5)%360)//45)
    directions=["北","东北","东","东南","南","西南","西","西北"]
    facing=directions[facing_index]
    sitting=directions[(facing_index+4)%8]
    return {"method":"玄空九宫年飞星基础盘","target_year":year,"built_year":built,"period":period,
            "facing_degrees":direction,"facing":facing,"sitting":sitting,"annual_center_star":center,
            "palaces":stars,"note":"此为年飞星基础盘，不等同完整宅盘。完整宅盘需精确坐向（最好罗盘度数）、建成/大修入伙时间、户型平面与门窗位置，并需确定玄空流派及兼向规则。"}
