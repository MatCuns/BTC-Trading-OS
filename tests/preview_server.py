"""Local browser QA ONLY: explicit in-memory store, never a production fallback."""

import uvicorn
from conftest import MemoryStore

from btc_os.api import create_app
from btc_os.config import Settings

if __name__ == "__main__":
    uvicorn.run(
        create_app(Settings(feed_mode="fixture", _env_file=None), MemoryStore()),
        host="127.0.0.1",
        port=8765,
    )
