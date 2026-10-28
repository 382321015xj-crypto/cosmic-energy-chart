from .product import calculate_product, InputError
from .location import search_locations, LocationError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
app=FastAPI(title='BaZi YongShen Engine',version='5.0.0-COSMIC')
@app.get('/',include_in_schema=False)
def frontend(): return FileResponse('web/index.html')
@app.get('/health')
def health(): return {'ok':True,'version':'5.0.0-COSMIC','address_scope':'global'}
@app.get('/api/v1/location/search')
def location_search(q:str=Query(...,min_length=1),limit:int=5):
    try: return {'results':search_locations(q,limit)}
    except LocationError as e: raise HTTPException(status_code=422,detail=str(e))
@app.post('/api/v1/bazi/calculate')
def calculate(payload:dict):
    try: return calculate_product(payload)
    except InputError as e: raise HTTPException(status_code=422,detail=str(e))
