from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from bloom_filter import BloomFilter
from model import InitRequest, ItemRequest, CheckResponse, StatsResponse
from fastapi.responses import RedirectResponse

bloom_filter: BloomFilter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize bloom filter on startup."""
    global bloom_filter
    expected_items = int(os.getenv("BLOOM_FILTER_EXPECTED_ITEMS", "10000"))
    false_positive_rate = float(os.getenv("BLOOM_FILTER_FALSE_POSITIVE_RATE", "0.01"))
    bloom_filter = BloomFilter(expected_items, false_positive_rate)
    yield


app = FastAPI(title="Bloom Filter Service", version="0.1.0", lifespan=lifespan)


@app.post("/init", response_model=StatsResponse)
async def init_bloom_filter(request: InitRequest):
    """Reinitialize the bloom filter with specified parameters."""
    global bloom_filter
    bloom_filter = BloomFilter(request.expected_items, request.false_positive_rate)
    return StatsResponse(**bloom_filter.get_stats())


@app.post("/add")
async def add_item(request: ItemRequest):
    """Add an item to the bloom filter."""
    bloom_filter.add(request.item)
    return {"message": f"Item '{request.item}' added successfully"}


@app.post("/check", response_model=CheckResponse)
async def check_item(request: ItemRequest):
    """Check if an item exists in the bloom filter."""
    exists = bloom_filter.check(request.item)
    return CheckResponse(item=request.item, exists=exists)


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get statistics about the bloom filter."""
    return StatsResponse(**bloom_filter.get_stats())


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root endpoint to the documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
