from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Assuming you have already set up your database URL
DATABASE_URL = "sqlite:///./inventory.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Get database session
db = SessionLocal()

# Execute the raw SQL query
items = db.execute(text("SELECT * FROM items")).fetchall()

# Print items
for item in items:
    print(item)

# Close the session
db.close()
