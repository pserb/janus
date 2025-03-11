from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Optional

from ...database import get_db
from ... import crud, schemas

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse)
def read_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    priority: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve paginated sources.

    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page
    - **is_active**: Filter active/inactive sources
    - **priority**: Filter by priority level (1=high, 2=medium, 3=low)
    """
    skip = (page - 1) * page_size
    sources = crud.get_sources(
        db=db, skip=skip, limit=page_size, is_active=is_active, priority=priority
    )
    total = len(
        sources
    )  # Simple count for now, might need optimization for large datasets

    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

    return {
        "items": sources,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{source_id}", response_model=schemas.Source)
def read_source(source_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Get a specific source by ID.
    """
    source = crud.get_source(db=db, source_id=source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@router.post("/", response_model=schemas.Source)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create a new source.
    """
    db_source = crud.get_source_by_name(db=db, name=source.name)
    if db_source:
        raise HTTPException(
            status_code=400, detail="Source with this name already exists"
        )

    return crud.create_source(db=db, source=source)


@router.put("/{source_id}", response_model=schemas.Source)
def update_source(
    source_id: int, source: schemas.SourceUpdate, db: Session = Depends(get_db)
) -> Any:
    """
    Update a source.
    """
    db_source = crud.update_source(db=db, source_id=source_id, source=source)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    return db_source


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Delete a source.
    """
    success = crud.delete_source(db=db, source_id=source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")

    return {"message": "Source deleted successfully"}
