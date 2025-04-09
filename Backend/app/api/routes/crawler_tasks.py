from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
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

# Use the async get_db dependency
db_dependency = Annotated[AsyncSession, Depends(get_db)]


@router.get("/tasks", response_model=CrawlerTaskList)
async def get_tasks(db: db_dependency, skip: int = Query(0), limit: int = Query(100)):
    """
    Retrieve all crawler tasks with pagination
    """
    query = select(CrawlerTask).offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return CrawlerTaskList(data=tasks, count=len(tasks))


@router.get("/tasks/{task_id}", response_model=CrawlerTaskResponse)
async def get_task(db: db_dependency, task_id: int):
    """
    Retrieve a specific crawler task by ID
    """
    query = select(CrawlerTask).filter(CrawlerTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks", response_model=CrawlerTaskResponse)
async def create_task(db: db_dependency, task: CrawlerTaskCreate):
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
    await db.commit()
    await db.refresh(new_task)
    return new_task


@router.put("/tasks/{task_id}", response_model=CrawlerTaskResponse)
async def update_task(db: db_dependency, task_id: int, task_update: CrawlerTaskUpdate):
    """
    Update an existing crawler task
    """
    query = select(CrawlerTask).filter(CrawlerTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    task.updated_at = datetime.now()
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/tasks/{task_id}/{action}", response_model=CrawlerTaskActionResponse)
async def execute_task_action(
    db: db_dependency, task_id: int, action: str, background_tasks: BackgroundTasks
):
    """
    Execute an action on a crawler task (start, stop, delete)
    """
    query = select(CrawlerTask).filter(CrawlerTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
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
        await db.delete(task)
        await db.commit()
        return {
            "success": True,
            "message": "Task deleted successfully",
            "task_id": task_id,
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    await db.commit()
    return {
        "success": True,
        "message": f"Task {action}ed successfully",
        "task_id": task_id,
    }


@router.get("/executions", response_model=TaskExecutionList)
async def get_task_executions(
    db: db_dependency,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
):
    """
    Retrieve task executions with pagination and optional filtering by task ID
    """
    query = select(TaskExecution)
    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    executions = result.scalars().all()

    return TaskExecutionList(data=executions, count=len(executions))


@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def get_task_execution(db: db_dependency, execution_id: int):
    """
    Retrieve a specific task execution by ID
    """
    query = select(TaskExecution).filter(TaskExecution.id == execution_id)
    result = await db.execute(query)
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Task execution not found")
    return execution


def append_log(current_log: str, new_message: str) -> str:
    """
    Append a new message to the current log with timestamp
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"{current_log}\n[{timestamp}] {new_message}"
        if current_log
        else f"[{timestamp}] {new_message}"
    )


async def execute_task(task_id: int):
    """
    Execute a crawler task asynchronously
    """
    # Create a new database session for this background task
    async with AsyncSession(engine) as db:
        # Get the task
        query = select(CrawlerTask).filter(CrawlerTask.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            logger.error(f"Task {task_id} not found")
            return

        # Create a new task execution record
        execution = TaskExecution(
            task_id=task_id,
            start_time=datetime.now(),
            status=TaskStatus.running,
            log="Task execution started",
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        try:
            # Update task status to running
            task.status = TaskStatus.running
            task.last_run_time = datetime.now()
            await db.commit()

            # Execute the task based on its function_name
            if task.function_name == "crawl_arxiv":
                # Parse parameters
                params = task.parameters
                if not params:
                    raise ValueError("No parameters provided for crawl_arxiv task")

                # Create ArxivApiArgs from parameters
                api_args = ArxivApiArgs(
                    query=params.get("query", ""),
                    max_results=params.get("max_results", 10),
                    sort_by=params.get("sort_by", "submittedDate"),
                    sort_order=params.get("sort_order", "descending"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date"),
                )

                # Create and run the crawler
                crawler = ArxivCrawler(api_args)
                papers = await crawler.crawl()

                # Process the results
                for paper in papers:
                    # Check if paper already exists
                    paper_query = select(ArxivPaper).filter(
                        ArxivPaper.arxiv_id == paper.arxiv_id
                    )
                    paper_result = await db.execute(paper_query)
                    existing_paper = paper_result.scalar_one_or_none()

                    if not existing_paper:
                        # Create new paper record
                        new_paper = ArxivPaper(
                            arxiv_id=paper.arxiv_id,
                            title=paper.title,
                            authors=paper.authors,
                            abstract=paper.abstract,
                            pdf_url=paper.pdf_url,
                            published=paper.published,
                            updated=paper.updated,
                            categories=paper.categories,
                        )
                        db.add(new_paper)

                # Update execution log
                execution.log = append_log(
                    execution.log, f"Successfully crawled {len(papers)} papers"
                )
                execution.status = TaskStatus.completed
            else:
                execution.log = append_log(
                    execution.log, f"Unknown function: {task.function_name}"
                )
                execution.status = TaskStatus.failed
        except Exception as e:
            logger.exception(f"Error executing task {task_id}: {str(e)}")
            execution.log = append_log(execution.log, f"Error: {str(e)}")
            execution.status = TaskStatus.failed
            task.status = TaskStatus.failed
        finally:
            # Update execution end time
            execution.end_time = datetime.now()
            await db.commit()

            # Update task status and next run time
            if task.repeat_type and task.status != TaskStatus.failed:
                # Calculate next run time based on repeat settings
                if task.repeat_type == "daily":
                    task.next_run_time = datetime.now() + timedelta(days=1)
                elif task.repeat_type == "weekly":
                    task.next_run_time = datetime.now() + timedelta(weeks=1)
                elif task.repeat_type == "monthly":
                    # Simple month addition (not perfect for month boundaries)
                    next_month = datetime.now().month + 1
                    next_year = datetime.now().year
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                    task.next_run_time = datetime(
                        next_year, next_month, datetime.now().day
                    )

                task.status = TaskStatus.pending
            else:
                task.status = TaskStatus.completed

            await db.commit()


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
