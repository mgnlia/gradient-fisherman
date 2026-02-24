"""File upload router — handles CSV ingestion."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents.ingest import parse_csv
from app.config import settings

router = APIRouter(prefix="/api", tags=["upload"])

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file for analysis.
    Returns dataset_id and schema summary.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    content = await file.read()
    
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB."
        )
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")
    
    try:
        result = parse_csv(content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse CSV: {str(e)}")


@router.get("/datasets/{dataset_id}/preview")
async def get_preview(dataset_id: str):
    """Get a preview of an uploaded dataset."""
    from app.agents.ingest import get_dataset
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    
    df = dataset["df"]
    return {
        "dataset_id": dataset_id,
        "filename": dataset["filename"],
        "rows": len(df),
        "columns": df.columns.tolist(),
        "preview": df.head(10).fillna("").to_dict(orient="records"),
        "schema_summary": dataset["schema_summary"],
    }
