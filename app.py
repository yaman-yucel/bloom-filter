from fastapi import FastAPI, HTTPException
from bloom_filter import BloomFilter
from model import InitRequest, ItemRequest, CheckResponse, StatsResponse


app = FastAPI(title="Bloom Filter Service", version="0.1.0")

bloom_filter: BloomFilter | None = None


@app.post("/init", response_model=StatsResponse)
async def init_bloom_filter(request: InitRequest):
    """Initialize the bloom filter with specified parameters."""
    global bloom_filter
    bloom_filter = BloomFilter(request.expected_items, request.false_positive_rate)
    return StatsResponse(**bloom_filter.get_stats())


@app.post("/add")
async def add_item(request: ItemRequest):
    """Add an item to the bloom filter."""
    if bloom_filter is None:
        raise HTTPException(status_code=400, detail="Bloom filter not initialized. Call /init first.")
    bloom_filter.add(request.item)
    return {"message": f"Item '{request.item}' added successfully"}


@app.post("/check", response_model=CheckResponse)
async def check_item(request: ItemRequest):
    """Check if an item exists in the bloom filter."""
    if bloom_filter is None:
        raise HTTPException(status_code=400, detail="Bloom filter not initialized. Call /init first.")
    exists = bloom_filter.check(request.item)
    return CheckResponse(item=request.item, exists=exists)


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get statistics about the bloom filter."""
    if bloom_filter is None:
        raise HTTPException(status_code=400, detail="Bloom filter not initialized. Call /init first.")
    return StatsResponse(**bloom_filter.get_stats())


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Bloom Filter Service",
        "version": "0.1.0",
        "endpoints": {
            "POST /init": "Initialize the bloom filter",
            "POST /add": "Add an item to the bloom filter",
            "POST /check": "Check if an item exists",
            "GET /stats": "Get bloom filter statistics",
        },
    }

