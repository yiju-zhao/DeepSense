from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.core.exceptions import DatabaseError
from app.core.logging import logger

@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for transaction management.
    
    Args:
        session: The database session to use.
        
    Yields:
        AsyncSession: The database session.
        
    Raises:
        DatabaseError: If a database operation fails.
    """
    # Start a nested transaction (savepoint)
    async with session.begin():
        try:
            # Yield the session to the context block
            yield session
            # The transaction will be committed when the context block exits normally
        except Exception as e:
            # Log the error
            logger.error(
                f"Transaction error: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            
            # The transaction will be rolled back automatically when an exception occurs
            # Re-raise as a DatabaseError
            if not isinstance(e, DatabaseError):
                raise DatabaseError(
                    message=f"Database operation failed: {str(e)}", 
                    details={"original_error": str(e)}
                )
            raise