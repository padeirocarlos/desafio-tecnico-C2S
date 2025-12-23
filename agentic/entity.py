import os
from pydantic import BaseModel, Field
from typing import Optional, Any
from strenum import StrEnum
from datetime import datetime

dt = datetime.now()

class EngineType(StrEnum):
    INLINE_4 = "inline_4"
    INLINE_6 = "inline_6"
    V6 = "v6"
    V8 = "v8"
    V12 = "v12"
    ELECTRIC = "electric"
    HYBRID = "hybrid"

class FuelType(StrEnum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"
    HYDROGEN = "hydrogen"

class TransmissionType(StrEnum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    DUAL_CLUTCH = "dual_clutch"

class Car(BaseModel):
    brand: str = Field( description="The manufacturer brand of the car", min_length=1)
    model: str = Field( description="The model name of the car", min_length=1)
    year: int = Field( description="The manufacturing year", ge=1900, le=dt.year)
    engine_type: EngineType = Field( description="The type of engine")
    fuel_type: FuelType = Field( description="The type of fuel the car uses")
    color: str = Field( description="The exterior color of the car")
    mileage: float = Field( description="The total distance traveled in kilometers", ge=0)
    number_of_doors: int = Field( description="The number of doors", ge=2, le=5)
    transmission: TransmissionType = Field( description="The type of transmission")
    price: Optional[float] = Field(None, description="The price in USD", ge=0)

class GeneralResult(BaseModel):
    answers: str = Field(description="< The information to perform a meaningful search>") 
    confidence: str = Field(description="< Here detailed classification of the confidence level of answer: High, Medium, or Low >")

class SqlQueryResult(BaseModel):
    comment: str = Field( description="<3-4 sentences explaining the propose of the sql query>")
    sql_query: str = Field( description="<final SQL to run>")
    confidence: str = Field(description="Here detailed classification of the confidence level of answer: High, Medium, or Low")

class FinalResult(BaseModel):
    final_response: str = Field(description="< Here detailed the final vehicle information well presented, formatted and displable in a friendly manner >")
    confidence: str = Field(description="Here detailed classification of the confidence level of answer: High, Medium, or Low")  

class Oold_FinalResult(BaseModel):
    description: str = Field(description="Here is a concise and friendly way to present the vehicles")
    final_response: str = Field(description="< Here detailed the final vehicle information well presented, formatted and displable in a friendly manner >")
    confidence: str = Field(description="Here detailed classification of the confidence level of answer: High, Medium, or Low")  
    
class SqlResult(BaseModel):
    comment: str = Field( description="<2-3 sentences explaining the meaning of the sql query result>")
    sql_result: str = Field( description="<final SQL Result well formatted>")
    
class SqlQueryPurifyResult(BaseModel):
    feedback: str = Field( description="<1-3 sentences explaining the gap or confirming correctness>")
    sql_purify: str = Field( description="<final SQL to run>")
    confidence: str = Field(description="Here detailed classification of the confidence level of answer: High, Medium, or Low")

class SearchJudgeResult(BaseModel):
    decision: str = Field( description=" Here the final decision whether to 'PRO' or 'REQ'")
    summary: str = Field( description="Here the essential details information (e.g., brand, Model, Year, Price)")
    issues_detected: str = Field( description= " Here the detailed missing or ambiguous information or fields ")
    confidence: str = Field(description="Here detailed classification of the confidence level of answer: High, Medium, or Low")
    validation_question: str =Field( description=" Here the validation question for a user is one that confirms their understanding or agreement before proceeding.")