import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_read_main():
    # Vi skapar en transport för att prata med din FastAPI-app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Vi testar /docs eftersom din main.py har en FastAPI app där
        response = await ac.get("/docs")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_lifespan_startup():
    # Kontrollera att appen har rätt titel från din main.py
    assert app.title == "riksdags_data"
    