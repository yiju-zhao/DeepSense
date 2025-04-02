from typing import Optional
from fastapi import Query


def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return")
) -> tuple[int, int]:
    """
    Get pagination parameters.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
        
    Returns:
        Tuple of (skip, limit)
    """
    return skip, limit


class PaginationParams:
    """
    Pagination parameters class for dependency injection.
    """
    
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of items to return")
    ):
        self.skip = skip
        self.limit = limit


class PaginatedResponse:
    """
    Paginated response class.
    """
    
    def __init__(
        self,
        items: list,
        total: int,
        skip: int,
        limit: int
    ):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit
        self.page = (skip // limit) + 1 if limit > 0 else 1
        self.pages = (total + limit - 1) // limit if limit > 0 else 1
        
    def dict(self):
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "items": self.items,
            "metadata": {
                "total": self.total,
                "page": self.page,
                "pages": self.pages,
                "skip": self.skip,
                "limit": self.limit,
                "has_more": self.page < self.pages
            }
        }