import random
import sqlite3
import pandas as pd
from typing import List, Optional
from agentic.entity import Car, EngineType, FuelType, TransmissionType

DB_SCHEMA =  """ 
        Table name: vehicles
        id (INTEGER PRIMARY)
        brand (TEXT NOT NULL)
        model (TEXT NOT NULL)
        year (INTEGER NOT NULL)
        engine_type (TEXT NOT NULL)
        fuel_type (TEXT NOT NULL)
        color (TEXT NOT NULL)
        mileage (REAL NOT NULL)
        number_of_doors (INTEGER NOT NULL)
        transmission (TEXT NOT NULL)
        price (REAL)
    """
# Data for generating random vehicles based on pre-defined brand of vehicles
BRANDS_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius", "Tacoma"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit", "Odyssey"],
    "Ford": ["F-150", "Mustang", "Explorer", "Escape", "Fusion", "Bronco"],
    "Chevrolet": ["Silverado", "Malibu", "Equinox", "Tahoe", "Corvette", "Camaro"],
    "BMW": ["3 Series", "5 Series", "X3", "X5", "7 Series", "M4"],
    "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLE", "GLC", "A-Class"],
    "Audi": ["A4", "A6", "Q5", "Q7", "A3", "Q3"],
    "Tesla": ["Model 3", "Model S", "Model X", "Model Y"],
    "Volkswagen": ["Jetta", "Passat", "Tiguan", "Atlas", "Golf", "ID.4"],
    "Nissan": ["Altima", "Sentra", "Rogue", "Pathfinder", "Maxima", "Leaf"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Kona", "Ioniq"],
    "Kia": ["Forte", "Optima", "Sportage", "Sorento", "Soul", "Telluride"],
    "Mazda": ["Mazda3", "Mazda6", "CX-5", "CX-9", "MX-5 Miata", "CX-30"],
    "Subaru": ["Outback", "Forester", "Crosstrek", "Impreza", "Ascent", "WRX"],
    "Lexus": ["ES", "RX", "NX", "IS", "GX", "UX"],
    "Porsche": ["911", "Cayenne", "Macan", "Panamera", "Taycan"],
    "Jeep": ["Wrangler", "Grand Cherokee", "Cherokee", "Compass", "Gladiator"],
    "Ram": ["1500", "2500", "3500"],
    "Volvo": ["XC90", "XC60", "S60", "V60", "XC40"],
    "Land Rover": ["Range Rover", "Discovery", "Defender", "Evoque"]
}

COLORS = [
    "White", "Black", "Silver", "Gray", "Red", "Blue", "Green", 
    "Yellow", "Orange", "Brown", "Beige", "Gold", "Purple", "Navy"
]

def db_details_schema(table_name:str = "vehicles", db_path: str="data/cars.db") -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    conn.close()
    
    return f"table name: {table_name}\n" + "\n".join([f"{r[1]} ({r[2]})" for r in rows])

def generate_car_data(data_size:int=150) -> List[Car]:
    """Generate 150 random car instances"""
    vehicles = []
    
    for i in range(data_size):
        brand = random.choice(list(BRANDS_MODELS.keys()))
        model = random.choice(BRANDS_MODELS[brand])
        year = random.randint(2015, 2025)
        
        # Determine engine and fuel type based on brand/model
        if brand == "Tesla":
            engine_type = EngineType.ELECTRIC
            fuel_type = FuelType.ELECTRIC
        elif "Prius" in model or "Ioniq" in model or random.random() < 0.15:
            engine_type = EngineType.HYBRID
            fuel_type = FuelType.HYBRID
        elif brand in ["BMW", "Mercedes-Benz", "Audi", "Porsche"] and random.random() < 0.3:
            engine_type = random.choice([EngineType.V6, EngineType.V8])
            fuel_type = FuelType.GASOLINE
        elif random.random() < 0.1:
            engine_type = EngineType.INLINE_4
            fuel_type = FuelType.DIESEL
        else:
            engine_type = random.choice([EngineType.INLINE_4, EngineType.INLINE_6, EngineType.V6])
            fuel_type = FuelType.GASOLINE
        
        color = random.choice(COLORS)
        mileage = round(random.uniform(0, 150000), 1)
        number_of_doors = random.choice([2, 4, 5])
        
        # Transmission based on brand and year
        if year >= 2020 and random.random() < 0.7:
            transmission = TransmissionType.AUTOMATIC
        elif brand in ["BMW", "Audi", "Porsche"] and random.random() < 0.2:
            transmission = TransmissionType.DUAL_CLUTCH
        elif random.random() < 0.15:
            transmission = TransmissionType.MANUAL
        else:
            transmission = random.choice([TransmissionType.AUTOMATIC, TransmissionType.CVT])
        
        # Price based on brand, year, and mileage
        base_prices = {
            "Toyota": 25000, "Honda": 24000, "Ford": 28000, "Chevrolet": 27000,
            "BMW": 45000, "Mercedes-Benz": 50000, "Audi": 43000, "Tesla": 48000,
            "Volkswagen": 23000, "Nissan": 22000, "Hyundai": 21000, "Kia": 22000,
            "Mazda": 24000, "Subaru": 26000, "Lexus": 42000, "Porsche": 75000,
            "Jeep": 32000, "Ram": 35000, "Volvo": 40000, "Land Rover": 55000
        }
        
        base_price = base_prices.get(brand, 25000)
        year_factor = (year - 2015) * 0.05 + 1
        mileage_factor = max(0.5, 1 - (mileage / 200000))
        price = round(base_price * year_factor * mileage_factor, 2)
        
        car = Car(
            brand=brand,
            model=model,
            year=year,
            engine_type=engine_type,
            fuel_type=fuel_type,
            color=color,
            mileage=mileage,
            number_of_doors=number_of_doors,
            transmission=transmission,
            price=price
        )
        
        vehicles.append(car)
    
    return vehicles

def create_database(db_path: str="data/cars.db"):
    """Create SQLite database and vehicles table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                engine_type TEXT NOT NULL,
                fuel_type TEXT NOT NULL,
                color TEXT NOT NULL,
                mileage REAL NOT NULL,
                number_of_doors INTEGER NOT NULL,
                transmission TEXT NOT NULL,
                price REAL
            )
    ''')
    conn.commit()
    return conn

def delete_vehicles(conn):
    cursor = conn.cursor()
    cursor.execute(''' DELETE FROM vehicles''')
    conn.commit()
    
def insert_vehicles(conn, vehicles: List[Car]):
    """Insert car data into database"""
    cursor = conn.cursor()
    
    for car in vehicles:
        cursor.execute('''
            INSERT INTO vehicles (brand, model, year, engine_type, fuel_type, color, 
                            mileage, number_of_doors, transmission, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            car.brand,
            car.model,
            car.year,
            car.engine_type.value,
            car.fuel_type.value,
            car.color,
            car.mileage,
            car.number_of_doors,
            car.transmission.value,
            car.price
        ))
    
    conn.commit()

def get_schema(db_path: str) -> str:
    """
    Return only the schema that the agent should use: 'transactions' table.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(transactions)")
    rows = cur.fetchall()
    conn.close()
    return "table name: transactions\n" + "\n".join([f"{r[1]} ({r[2]})" for r in rows])

def initialize_cars_db():
    conn = create_database()
    global DB_SCHEMA
    DB_SCHEMA = db_details_schema()
    data = generate_car_data()
    delete_vehicles(conn)
    insert_vehicles(conn, vehicles=data)
