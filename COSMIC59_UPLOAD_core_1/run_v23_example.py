from datetime import datetime
from pprint import pprint
from app.full_engine import calculate_full

result=calculate_full(
    local_dt=datetime(2000,1,7,14,0),
    longitude=120.0,
    iana_timezone='Asia/Shanghai',
    gender='male',
    target_year=2026,
)
pprint(result)
