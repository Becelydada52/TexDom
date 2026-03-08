from __future__ import annotations

import uvicorn

from app.web.app import app


if __name__ == "__main__":
    uvicorn.run("main_web:app", host="0.0.0.0", port=5000, reload=False)

