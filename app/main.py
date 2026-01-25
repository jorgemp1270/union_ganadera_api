from fastapi import FastAPI
from .routers import users, bovinos, files, domicilios, predios
from .routers import eventos_main
from .routers.eventos import pesos, dietas, vacunaciones, desparasitaciones, laboratorios, compraventas, traslados, enfermedades, tratamientos
from .database import engine
from . import models

# Create tables (if they don't exist, though docker-compose init script should handle it)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Union Ganadera API")

app.include_router(users.router)
app.include_router(bovinos.router)
app.include_router(eventos_main.router)
app.include_router(pesos.router)
app.include_router(dietas.router)
app.include_router(vacunaciones.router)
app.include_router(desparasitaciones.router)
app.include_router(laboratorios.router)
app.include_router(compraventas.router)
app.include_router(traslados.router)
app.include_router(enfermedades.router)
app.include_router(tratamientos.router)
app.include_router(files.router)
app.include_router(domicilios.router)
app.include_router(predios.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Union Ganadera API"}
