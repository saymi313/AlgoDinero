# Environment Variables

Create a `.env` file in this folder (`Backend/source_code`) with:

```
MONGODB_URI=mongodb+srv://usairamsaeed:<db_password>@algodinero.qtamhh.mongodb.net/?retryWrites=true&w=majority&appName=AlgoDinero
```

The API loads `.env` automatically at startup. Alternatively, set it via PowerShell:

```
setx MONGODB_URI "mongodb+srv://usairamsaeed:<1234>@algodinero.qtamhh.mongodb.net/?retryWrites=true&w=majority&appName=AlgoDinero"
```


