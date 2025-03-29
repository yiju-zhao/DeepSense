import datetime
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Query
router = APIRouter(prefix="/tasks", tags=["tasks"])

from database import SessionLocal
from models.tasks import CrawlerTask, CrawlerTaskActionResponse, CrawlerTaskCreate, CrawlerTaskList, CrawlerTaskResponse, TaskStatus

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/crawler", response_model=CrawlerTaskList)
def get_tasks(db: db_dependency, skip: int = Query(0), limit: int = Query(100)):
    """
    Retrieve crawler tasks.
    """
    session = SessionLocal()
    tasks = db.query(CrawlerTask).offset(skip).limit(limit).all()
    return CrawlerTaskList(data=tasks, count=len(tasks))

@router.get("/{task_id}", response_model=CrawlerTaskResponse)
def get_task(db: db_dependency, task_id: int):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=CrawlerTaskResponse)
def create_task(db: db_dependency, task: CrawlerTaskCreate):
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
        next_run_time=task.next_run_time or datetime.datetime.now()
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# 启动、暂停、停止或删除任务
@router.post("/{task_id}/{action}", response_model=CrawlerTaskActionResponse)
def task_action(db: db_dependency, task_id: int, action: str):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if action == "start":
        if task.status == TaskStatus.running:
            raise HTTPException(status_code=400, detail="Task is already running")
        task.status = TaskStatus.running
        task.start_time = datetime.datetime.now()
        task.log = "Task started"
    elif action == "pause":
        if task.status != TaskStatus.running:
            raise HTTPException(status_code=400, detail="Task is not running")
        task.status = TaskStatus.stopped
        task.log = "Task paused"
    elif action == "stop":
        if task.status != TaskStatus.running:
            raise HTTPException(status_code=400, detail="Task is not running")
        task.status = TaskStatus.stopped
        task.end_time = datetime.datetime.now()
        task.log = "Task stopped"
    elif action == "delete":
        db.delete(task)
        db.commit()
        return {"message": "Task deleted successfully","task_id": task_id}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    db.commit()
    return {"message": f"Task {action}ed successfully", "task_id": task_id}