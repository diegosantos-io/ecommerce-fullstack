from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.categories import router as categories_router
from app.routers.users import router as users_router
from app.routers.products import router as products_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.password_reset import router as password_reset_router

app = FastAPI(
    title="E-commerce API",
    description="API REST para plataforma de e-commerce",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(password_reset_router)


@app.get("/")
def root():
    return {
        "message": "E-commerce API está funcionando!"
    }
