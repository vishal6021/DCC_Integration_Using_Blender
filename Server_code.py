import os
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import FileResponse
import time
import logging
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup (SQLite with SQLAlchemy)
DATABASE_URL = "sqlite:///./inventory.db"  # SQLite database file

# Create database engine and sessionmaker
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Models (SQLAlchemy)
class ItemModel(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    quantity = Column(Integer)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic Models for Input Validation
class TransformData(BaseModel):
    position: list[float]
    rotation: list[float]
    scale: list[float]

class TranslationData(BaseModel):
    position: list[float]

class RotationData(BaseModel):
    rotation: list[float]

class ScaleData(BaseModel):
    scale: list[float]

class Item(BaseModel):
    name: str
    quantity: int

class UpdateQuantity(BaseModel):
    name: str
    new_quantity: int

# Helper function to simulate a 10-second delay
def simulate_delay():
    if os.getenv("ENABLE_DELAY", "false").lower() == "true":
        time.sleep(10)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI server!"}

# Favicon endpoint
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

# Endpoint: /transform
@app.post("/transform")
async def transform(data: TransformData):
    logger.info(f"Received transform data: {data}")
    simulate_delay()
    return {"message": "Transform data received", "data": data}

# Endpoint: /translation
@app.post("/translation")
async def translation(data: TranslationData):
    logger.info(f"Received translation data: {data}")
    simulate_delay()
    return {"message": "Translation data received", "data": data}

# Endpoint: /rotation
@app.post("/rotation")
async def rotation(data: RotationData):
    logger.info(f"Received rotation data: {data}")
    simulate_delay()
    return {"message": "Rotation data received", "data": data}

# Endpoint: /scale
@app.post("/scale")
async def scale(data: ScaleData):
    logger.info(f"Received scale data: {data}")
    simulate_delay()
    return {"message": "Scale data received", "data": data}

# Endpoint: /file-path
@app.get("/file-path")
async def file_path(projectpath: Optional[bool] = Query(None, description="Set to true to get project folder path")):
    logger.info(f"Received request for file path. Project path requested: {projectpath}")
    simulate_delay()
    if projectpath:
        return {"message": "Project folder path", "path": "/path/to/project/folder"}
    else:
        return {"message": "DCC file path", "path": "/path/to/dcc/file"}

# Endpoint: /add-item
@app.post("/add-item")
async def add_item(item: Item, db: Session = Depends(get_db)):
    logger.info(f"Received request to add item: {item}")

    # Debugging: Print incoming data
    print(f"Adding Item: Name={item.name}, Quantity={item.quantity}")

    simulate_delay()

    # Check if item already exists
    db_item = db.query(ItemModel).filter(ItemModel.name == item.name).first()
    if db_item:
        raise HTTPException(status_code=400, detail="Item already exists")

    # Add the new item to the database
    db_item = ItemModel(name=item.name, quantity=item.quantity)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Debugging: Print database values after commit
    print(f"Item added to DB: Name={db_item.name}, Quantity={db_item.quantity}")

    return {"message": "Item added", "item": item}


# Endpoint: /remove-item
@app.delete("/remove-item")
async def remove_item(name: str, db: Session = Depends(get_db)):
    logger.info(f"Received request to remove item: {name}")
    simulate_delay()

    # Find item in the database
    db_item = db.query(ItemModel).filter(ItemModel.name == name).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Remove the item from the database
    db.delete(db_item)
    db.commit()

    return {"message": "Item removed", "name": name}

# Endpoint: /update-quantity
@app.put("/update-quantity")
async def update_quantity(data: UpdateQuantity, db: Session = Depends(get_db)):
    logger.info(f"Received request to update quantity: {data}")
    simulate_delay()

    # Find item in the database
    db_item = db.query(ItemModel).filter(ItemModel.name == data.name).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update the item's quantity
    db_item.quantity = data.new_quantity
    db.commit()
    db.refresh(db_item)

    return {"message": "Quantity updated", "item": {"name": data.name, "quantity": data.new_quantity}}

# Endpoint: /list-items
@app.get("/list-items")
async def list_items(db: Session = Depends(get_db)):
    logger.info("Received request to list all items.")
    simulate_delay()

    # Fetch all items from the database
    items = db.query(ItemModel).all()
    return {"items": items}

# Endpoint: /get-item
@app.get("/get-item")
async def get_item(name: str, db: Session = Depends(get_db)):
    logger.info(f"Received request to get item: {name}")
    simulate_delay()

    # Fetch the item by name from the database
    db_item = db.query(ItemModel).filter(ItemModel.name == name).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"item": db_item}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)