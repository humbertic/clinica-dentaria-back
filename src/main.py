from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utilizadores.router import router as utilizadores_router
from src.perfis.router import router as perfis_router
from src.auditoria.router import router as auditoria_router
from src.clinica.router import router as clinica_router
from src.stock.router import router as stock_router

app = FastAPI(
    title="Clínica Dentária API",
    description="API para gestão de utilizadores, perfis e autenticação da clínica dentária.",
    version="1.0.0",
    contact={
        "name": "Nome da Clínica",
        "email": "contato@clinicadentaria.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.1.122:3000"],  # ajuste conforme seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["default"])
def root():
    return {
        "message": "Bem-vindo à API da Clínica Dentária!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

app.include_router(utilizadores_router, prefix="/utilizadores",tags=["utilizadores"])
app.include_router(perfis_router, prefix="/perfis", tags=["perfis"])
app.include_router(clinica_router, prefix="/clinica", tags=["clinica"])
app.include_router(auditoria_router, prefix="/auditoria", tags=["auditoria"])
app.include_router(stock_router, prefix="/stock", tags=["stock"])



