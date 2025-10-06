import uvicorn


if __name__ == "__main__":
    # Run the FastAPI app using uvicorn, similar to "python filename.py"
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
    )


