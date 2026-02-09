import asyncio
import requests

def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

async def process_data(data):
    # Simulated data processing
    await asyncio.sleep(1)  # Simulate I/O operation
    return {"processed": data}

async def main():
    url = "http://api.example.com/data"
    try:
        data = await fetch_data(url)
        result = await process_data(data)
        print(result)
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())