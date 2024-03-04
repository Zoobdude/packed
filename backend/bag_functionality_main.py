from fastapi import FastAPI
from pydantic import BaseModel

from tinydb import TinyDB, where
from fastapi import HTTPException

app = FastAPI()
item_db = TinyDB('items.json')
bag_db = TinyDB('bags.json')

#record structure

class Item(BaseModel):
    item_name: str
    description: str = None
    importance: int = 0
    home_location: str
    away_from_home: bool = False
    
    bag_in: str = None

class Bag(BaseModel):
    bag_name: str
    location: str
    description: str = None

@app.post('/add_item')
async def add_item(Item: Item):
    if item_db.search(where('item_name') == Item.item_name):
        raise HTTPException(status_code=409, detail='Item already exists')
    
    if Item.bag_in:
        if not bag_db.search(where('bag_name') == Item.bag_in):
            raise HTTPException(status_code=404, detail='Bag does not exist')
    
    if Item.away_from_home and not Item.bag_in:
        raise HTTPException(status_code=400, detail='Item cannot be away from home without being in a bag')
    
    item_id = item_db.insert(Item.dict())
    return {'id': item_id}

@app.post('/add_bag')
async def add_bag(Bag: Bag):
    if bag_db.search(where('bag_name') == Bag.bag_name):
        raise HTTPException(status_code=409, detail='Bag already exists')
    
    bag_id = bag_db.insert(Bag.dict())
    return {'id': bag_id}

@app.get('/items')
async def get_items(bag_in: str = None,
                    away_from_home: bool = None,
                    offset: int = 0,
                    limit: int = None, ):
    if bag_in:
        if not bag_db.search(where('bag_name') == bag_in):
            raise HTTPException(status_code=404, detail='Bag does not exist')
    
    if away_from_home and bag_in:
        items = items.db.search((where('away_from_home') == away_from_home) & (where('bag_in') == bag_in))
    
    elif bag_in:
        items = item_db.search(where('bag_in') == bag_in)
    
    elif away_from_home:
        items = item_db.search(where('away_from_home') == away_from_home)
    
    else:
        items = item_db.all()
    
    if limit:
        if offset+limit > len(item_db):
            end = len(item_db)
        else:
            end = offset+limit
    
    else:
        end = len(item_db)
        
    return sorted(items[offset:end], key=lambda x: x['importance'], reverse=True)

@app.get('/bags')
async def get_bags():
    return bag_db.all()

@app.patch('/move_item/{item}')
async def move_item(item: str, away_from_home: bool, bag_in: str = None):
    if not item_db.search(where('item_name') == item):
        raise HTTPException(status_code=404, detail='Item does not exist')
    
    if bag_in:
        if not bag_db.search(where('bag_name') == bag_in):
            raise HTTPException(status_code=404, detail='Bag does not exist')
    
    if away_from_home and not bag_in:
        raise HTTPException(status_code=400, detail='Item cannot be away from home without being in a bag')
    
    item_db.update({'away_from_home': away_from_home, 'bag_in': bag_in}, where('item_name') == item)
    return {'message': 'item moved'}

@app.patch('/move_bag/{bag}')
async def move_bag(bag: str, location: str):
    if not bag_db.search(where('bag_name') == bag):
        raise HTTPException(status_code=404, detail='Bag does not exist')
    
    bag_db.update({'location': location}, where('bag_name') == bag)
    return {'message': 'bag moved'}