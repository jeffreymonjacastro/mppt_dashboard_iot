from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",                  
    "https://mppt-dashboard-iot.vercel.app", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,      
    allow_methods=["*"],         
    allow_headers=["*"],         
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
def hello_name(name: str):
    return {"message": f"Hello {name}"}
