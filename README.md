# Expression Data API

A lightweight Flask service that exposes gene expression and metadata queries over HTTP.  
Clients can fetch per‑gene expression profiles, batch query multiple IDs with selected conditions, and retrieve dataset metadata.

## Prerequisites

1. **Python 3.8+**
2. **Flask**
3. **Pandas**
4. **Gunicorn**

## Project Structure & Data Organization

```bash
project-root/
├── app.py # Defines Flask routes/endpoints
├── functions.py # Core business logic for data retrieval
├── constants.py # Required column sets and base data directory
├── utils.py # CSV loading helper (read_dataset)
```

## Configuration Notes

- Database directory

  Edit the ruta variable in `constants.py` or define your own `BASE_DIR` environment variable.

- Port

  - By default it is on port 4002, but you can set it to the port of your choice.

    ```bash
    app.run(host="0.0.0.0", port=####)
    ```

## Run the Flask app

```bash
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=4002
```

or simply:

```bash
python app.py
```

The service will listen on 0.0.0.0:4002.

## API Endpoints

1. Get expression for one gene:

   `GET /expression/gene/<dataset>/<gene_id>`

   - Path parameters

     - `dataset` (string): name of the CSV file (relative to `BASE_DIR`)

     - `gene_id` (string): gene identifier to query

2. Batch query gene/transcript IDs

   `POST /expression/gene/ids`

   - Request JSON body:

     ```json
     {
        "dataset": "dataset1.csv",
        "gene_ids": ["GENE1", "TRANS2", "GENE3"],
        "columns": ["condA", "condB", "condC
     }
     ```

3. Get dataset metadata

   `GET /expression/metadata/<dataset>`

   - Path parameter

     - `dataset` (string): CSV file name

Responses:

- 200 OK → JSON {status:"sucess", message:"...", result: "...{('Check in functions.py')}..."}

- 4xx/5xx → JSON { status: "error", message: "..." }
