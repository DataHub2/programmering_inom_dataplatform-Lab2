import httpx
from config.settings import RIKSDAGEN_APIS, HEADERS

async def fetch_data(source: str):

    if source not in RIKSDAGEN_APIS:
        raise ValueError("Ogiltig datakälla")

    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        response = await client.get(RIKSDAGEN_APIS[source])
        response.raise_for_status()
        return response.json()