from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models.tasks import (
    ArxivPaper,
    CrawlerTask,
    CrawlerTaskActionResponse,
    CrawlerTaskCreate,
    CrawlerTaskList,
    CrawlerTaskResponse,
    CrawlerTaskUpdate,
    TaskExecution,
    TaskExecutionList,
    TaskExecutionResponse,
    TaskStatus,
)
from core.arxiv_crawler import ArxivApiArgs, ArxivCrawler

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawler", tags=["crawler"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/tasks", response_model=CrawlerTaskList)
def get_tasks(db: db_dependency, skip: int = Query(0), limit: int = Query(100)):
    """
    Retrieve all crawler tasks with pagination
    """
    tasks = db.query(CrawlerTask).offset(skip).limit(limit).all()
    return CrawlerTaskList(data=tasks, count=len(tasks))


@router.get("/tasks/{task_id}", response_model=CrawlerTaskResponse)
def get_task(db: db_dependency, task_id: int):
    """
    Retrieve a specific crawler task by ID
    """
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks", response_model=CrawlerTaskResponse)
def create_task(db: db_dependency, task: CrawlerTaskCreate):
    """
    Create a new crawler task
    """
    new_task = CrawlerTask(
        name=task.name,
        description=task.description,
        function_name=task.function_name,
        parameters=task.parameters,
        start_time=task.start_time,
        end_time=task.end_time,
        status=TaskStatus.pending,
        repeat_type=task.repeat_type,
        repeat_interval=task.repeat_interval,
        next_run_time=task.next_run_time,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.put("/tasks/{task_id}", response_model=CrawlerTaskResponse)
def update_task(db: db_dependency, task_id: int, task_update: CrawlerTaskUpdate):
    """
    Update an existing crawler task
    """
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    task.updated_at = datetime.now()
    db.commit()
    db.refresh(task)
    return task


@router.post("/tasks/{task_id}/{action}", response_model=CrawlerTaskActionResponse)
async def execute_task_action(
    db: db_dependency, 
    task_id: int, 
    action: str, 
    background_tasks: BackgroundTasks
):
    """
    Execute an action on a crawler task (start, stop, delete)
    """
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if action == "start":
        if task.status == TaskStatus.running:
            raise HTTPException(status_code=400, detail="Task is already running")
        task.status = TaskStatus.running.value
        task.start_time = datetime.now()
        background_tasks.add_task(execute_task, task.id)

    elif action == "stop":
        if task.status != TaskStatus.running:
            raise HTTPException(status_code=400, detail="Task is not running")
        task.status = TaskStatus.stopped.value
        task.end_time = datetime.now()
        
    elif action == "delete":
        db.delete(task)
        db.commit()
        return {
            "success": True,
            "message": "Task deleted successfully",
            "task_id": task_id,
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    db.commit()
    return {
        "success": True,
        "message": f"Task {action}ed successfully",
        "task_id": task_id,
    }


@router.get("/executions", response_model=TaskExecutionList)
def get_task_executions(
    db: db_dependency,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
):
    """
    Get execution history for crawler tasks with optional filtering
    """
    query = db.query(TaskExecution)

    if task_id is not None:
        query = query.filter(TaskExecution.task_id == task_id)

    total_count = query.count()
    executions = (
        query.order_by(TaskExecution.created_at.desc()).offset(skip).limit(limit).all()
    )

    return TaskExecutionList(data=executions, count=total_count)


@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
def get_task_execution(db: db_dependency, execution_id: int):
    """
    Get details of a specific task execution
    """
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Task execution with ID {execution_id} not found",
        )
    return execution


# Helper functions for task execution
def append_log(current_log: str, new_message: str) -> str:
    """Helper function to append messages to execution log"""
    if current_log:
        return f"{current_log}\n{new_message}"
    return new_message


async def execute_task(task_id: int):
    """
    Background function to execute a crawler task
    """
    db = next(get_db())
    try:
        logger.info(f"Starting task execution: {task_id}")
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"Task not found: {task_id}")
            return

        # Create execution record
        execution = TaskExecution(
            task_id=task_id,
            status=TaskStatus.pending.value,
            start_time=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db.add(execution)

        # Get task function
        func = task_function_mapping.get(task.function_name)
        logger.info(f"Using task function: {task.function_name}")
        if not func:
            task.status = TaskStatus.failed.value
            execution.log = append_log(
                execution.log, f"Function not found: {task.function_name}"
            )
            db.commit()
            return

        # Update status to running
        task.status = TaskStatus.running.value
        task.start_time = datetime.now()
        execution.status = TaskStatus.running.value
        execution.log = append_log(execution.log, f"Task started: {task.name}")
        execution.log = append_log(execution.log, f"Parameters: {task.parameters}")
        db.commit()

        # Execute the task function
        result = func(task)

        if result.get("status") == "error":
            raise Exception(result.get("message"))
            
        execution.log = append_log(execution.log, "Task executed successfully")
        execution.status = TaskStatus.completed.value
        execution.end_time = datetime.now()

        # Update task status
        task.status = TaskStatus.completed.value
        task.end_time = datetime.now()
        logger.info(f"Task completed: {task.name}")

        # Process and store results
        logger.info("Storing results in database")
        execution.log = append_log(execution.log, "Storing results in database")
        
        if result.get("data") and result.get("data").get("papers"):
            papers_count = 0
            duplicate_count = 0
            total_count = len(result.get("data").get("papers"))
            logger.info(f"Found {total_count} papers to process")
            
            for paper_data in result.get("data").get("papers"):
                # Check for duplicates
                logger.info(f"Processing paper: {paper_data.get('arxiv_id')}")
                existing_paper = (
                    db.query(ArxivPaper)
                    .filter(ArxivPaper.arxiv_id == paper_data.get("arxiv_id"))
                    .first()
                )
                
                if existing_paper:
                    logger.info(f"Skipping duplicate paper: {paper_data.get('arxiv_id')}")
                    execution.log = append_log(
                        execution.log, f"Skipping duplicate paper: {paper_data.get('arxiv_id')}"
                    )
                    duplicate_count += 1
                    continue
                
                # Create new paper record
                logger.info(f"Saving paper: {paper_data.get('arxiv_id')}")
                execution.log = append_log(
                    execution.log, f"Saving paper: {paper_data.get('arxiv_id')}"
                )
                new_paper = ArxivPaper(
                    arxiv_id=paper_data.get("arxiv_id"),
                    title=paper_data.get("title"),
                    pdf_url=paper_data.get("pdf_url"),
                    published=paper_data.get("published"),
                    summary=paper_data.get("summary"),
                    authors=paper_data.get("authors"),
                    primary_category=paper_data.get("primary_category"),
                    categories=paper_data.get("categories"),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(new_paper)
                papers_count += 1

            db.commit()
            execution.log = append_log(
                execution.log,
                f"Saved {papers_count} papers to database, skipped {duplicate_count} duplicates"
            )
            logger.info(
                f"Saved {papers_count} papers to database, skipped {duplicate_count} duplicates"
            )
        else:
            logger.info("No papers found to save")
            execution.log = append_log(execution.log, "No papers found to save")

    except Exception as e:
        # Handle failures
        if 'execution' in locals():
            execution.status = TaskStatus.failed.value
            execution.end_time = datetime.now()
            execution.log = append_log(execution.log, str(e))
        logger.error(f"Error executing task {task_id}: {str(e)}")

        if 'task' in locals():
            task.status = TaskStatus.failed.value
    finally:
        # Update last run time and handle repeating tasks
        if 'task' in locals():
            task.last_run_time = datetime.now()
            if task.repeat_type:
                task.update_next_run_time()
                task.status = TaskStatus.pending.value

        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            db.rollback()
        finally:
            db.close()


def crawl_arxiv(task: CrawlerTask):
    """
    Function to crawl papers from arXiv
    
    Args:
        task: The crawler task containing parameters
    
    Returns:
        dict: Result of the crawling operation
    """
    try:
        crawler = ArxivCrawler()
        logger.info(f"Crawling arXiv data, task_id={task.id}")
        
        # Get URL parameter
        url = task.parameters.get("url", "")
        if not url:
            raise ValueError("URL is required")
            
        # Other parameters
        args = ArxivApiArgs(
            search_query=task.parameters.get("query", ""),
            start=task.parameters.get("start", 0),
            max_results=task.parameters.get("max_results", 10),
            sortBy=task.parameters.get("sortBy", "submittedDate"),
            sortOrder=task.parameters.get("sortOrder", "descending"),
        )
        
        logger.info(f"Crawler parameters: url={url}, args={args}")
        
        # Execute API call
        results = crawler.get_api_response(url, args)
        if not results:
            raise ValueError("No results found")
            
        return {
            "status": "success",
            "message": "Crawling completed successfully",
            "data": results,
        }
    except Exception as e:
        logger.error(f"Error crawling arXiv: {str(e)}")
        return {"status": "error", "message": str(e), "data": None}


# Map task function names to functions
task_function_mapping = {
    "crawl_arxiv": crawl_arxiv,
} 