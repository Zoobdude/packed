from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from tinydb import TinyDB, where
from fastapi import HTTPException

app = FastAPI()
item_db = TinyDB('items.json')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#record structure

class Item(BaseModel):
    item_name: str
    description: str = None
    importance: int = 2 # 1=low, 2=medium, 3=high
    away_from_home: bool = False


@app.post('/add_item')
async def add_item(Item: Item):
    if item_db.search(where('item_name') == Item.item_name):
        raise HTTPException(status_code=409, detail='Item already exists')

    
    item_id = item_db.insert(Item.model_dump())
    return {'id': item_id}


@app.get('/items')
async def get_items(away_from_home: bool = None,
                    offset: int = 0,
                    limit: int = None, ):
    
    
    if away_from_home is True:
        items = item_db.search(where('away_from_home') == True)
    elif away_from_home is False:
        items = item_db.search(where('away_from_home') == False)
    else:
        items = item_db.all()
    
    if limit:
        if offset+limit > len(item_db):
            end = len(item_db)
        else:
            end = offset+limit
    
    else:
        end = len(item_db)
    
    retu = sorted(items[offset:end], key=lambda x: x['importance'], reverse=True)
    
    print(retu)
    return retu

@app.patch('/move_item/{item}')
async def toggle_item_location(item: str):
    if not item_db.search(where('item_name') == item):
        raise HTTPException(status_code=404, detail='Item does not exist')
    
    current = item_db.search(where('item_name') == item)[0]
    current['away_from_home'] = not current['away_from_home']
    item_db.update(current, where('item_name') == item)
    
    return {'away_from_home': current['away_from_home']}

@app.delete('/delete_item/{item}')
async def delete_item(item: str):
    if not item_db.search(where('item_name') == item):
        raise HTTPException(status_code=404, detail='Item does not exist')
    
    item_db.remove(where('item_name') == item)
    return {'deleted': item}