from datetime import datetime
from .casting import cast_birth
from .dayun import build_dayun
from .dynamic import dynamic_analysis

def calculate_full(local_dt:datetime, longitude:float, iana_timezone:str, gender:str, target_year=None):
    chart=cast_birth(local_dt,longitude,iana_timezone,gender)
    dy=build_dayun(local_dt,iana_timezone,chart['four_pillars']['month']['text'],chart['four_pillars']['year']['stem'],gender)
    chart['da_yun']=dy
    if target_year is not None:
        chart['liu_nian']=dynamic_analysis(chart,dy,target_year)
    chart['engine']['version']='5.0.0'
    chart['engine']['dynamic_rule_set']='DYNAMIC_V1'
    return chart
