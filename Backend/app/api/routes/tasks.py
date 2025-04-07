from datetime import date, datetime, timezone
import logging
import sys
import uuid
from typing import Annotated, Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, logger
from sqlalchemy.orm import Session, load_only
from fastapi import Query
router = APIRouter(prefix="/tasks", tags=["tasks"])

from core.review_arxiv_paper import ReviewArxivPaper
from core.arxiv_crawler import ArxivApiArgs, ArxivCrawler
from database import SessionLocal
from models.tasks import ArxivPaper, CrawlerTask, CrawlerTaskActionResponse, CrawlerTaskCreate, CrawlerTaskList, CrawlerTaskResponse, CrawlerTaskUpdate, PaperScores, Publication, StandardResponse, TaskExecution, TaskExecutionList, TaskExecutionResponse, TaskStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
# Create logger for this module
logger = logging.getLogger(__name__)

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
    tasks = db.query(CrawlerTask).offset(skip).limit(limit).all()
    return CrawlerTaskList(data=tasks, count=len(tasks))

@router.get("/crawler/executions", response_model=TaskExecutionList)
def get_task_executions(
    db: db_dependency,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    task_id: Optional[int] = Query(None, description="Filter by task ID")
):
    """
    Get all task execution records with optional filtering by task_id
    """
    query = db.query(TaskExecution)
    
    # Apply task_id filter if provided
    if task_id is not None:
        query = query.filter(TaskExecution.task_id == task_id)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    executions = query.order_by(TaskExecution.created_at.desc()) \
                     .offset(skip) \
                     .limit(limit) \
                     .all()
    
    return TaskExecutionList(
        data=executions,
        count=total_count
    )

@router.get("/crawler/executions/{execution_id}", response_model=TaskExecutionResponse)
def get_task_execution(
    db: db_dependency,
    execution_id: int
):
    """
    Get a specific task execution record by ID
    """
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Task execution record with ID {execution_id} not found"
        )
    return execution

@router.get("/crawler/{task_id}", response_model=CrawlerTaskResponse)
def get_task(db: db_dependency, task_id: int):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/crawler/{task_id}", response_model=CrawlerTaskResponse)
def get_task(db: db_dependency, task_id: int):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/task/", response_model=CrawlerTaskResponse)
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
        next_run_time=task.next_run_time,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.put("/task/{task_id}", response_model=CrawlerTaskResponse)
def update_task(
    db: db_dependency,
    task_id: int,
    task_update: CrawlerTaskUpdate
):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task

# 启动/停止或删除任务
@router.post("/task/{task_id}/{action}", response_model=CrawlerTaskActionResponse)
async def task_action(db: db_dependency, task_id: int, action: str, background_tasks: BackgroundTasks):
    task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if action == "start":
        if task.status == TaskStatus.running:
            raise HTTPException(status_code=400, detail="Task is already running")
        task.status = TaskStatus.running.value
        task.start_time = datetime.now()
        # 将后台任务加入 BackgroundTasks 队列，异步执行任务
        background_tasks.add_task(execute_task, task.id)

    elif action == "stop":
        #TODO: Implement stop logic
        pass
    elif action == "delete":
        #TODO: Implement delete logic
        # 删除任务,要先停止任务
        db.delete(task)
        db.commit()
        return {"success":True, "message": "Task deleted successfully","task_id": task_id}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    db.commit()
    return {"success":True, "message": f"Task {action}ed successfully", "task_id": task_id}


@router.get("/paper/{paper_id}", response_model=StandardResponse)
async def get_paper_by_id(db: db_dependency, paper_id: str):
    """
    retrive a paper from db, contains paper basic info and the AI scores
    """    
    publication = (
        db.query(Publication)
        .outerjoin(PaperScores, Publication.paper_id == PaperScores.paper_id)
        .filter(Publication.paper_id == paper_id)
        .first()
    )
    # TODO 备注： 当前arxiv的部分元数据，比如作者和affiliation 还没有被转化到主数据表，当前暂且从arxiv 里面单独查询出来
    arxiv_paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id== paper_id).first()
   
    if publication and arxiv_paper:
         # TODO: 全部返回给前端不合适，pdf 的raw data 太长了。另外，论文作者也待处理。 后续可以考虑直接建一个view
        publication.content_raw_text = '' # 粗暴处理 remove it
        publication.reference_raw_text =''
        return_data = {
            'paper_id':publication.paper_id,
            'publish_date':publication.publish_date,
            'title':publication.title,
            'pdf_url':publication.pdf_url,
            'abstract':publication.abstract,
            'author':arxiv_paper.authors,
            'conclusion':publication.conclusion,
            'traige_qa':publication.triage_qa,
            'scores':publication.scores if publication.scores else "{'review_status':'pending','error_message':'not processed yet'}",
            'weighted_score': publication.scores.weighted_score if publication.scores else 0
        }
        
       
        return StandardResponse(
            success=True,
            message=f"Paper with ID {paper_id} retrieved successfully.",
            data=return_data)
    else:
        return StandardResponse(
            success=False,
            message=f"Paper with ID {paper_id} not found.",
            data={})

@router.get("/papers", response_model=StandardResponse)
async def get_all_papers(
    db: db_dependency,
    start_date: Optional[date] = Query("publish_date", description="start date to filter by, None means search all"),
    end_date: Optional[date] = Query("publish_date", description="end date to filter by, None means to now"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    sort_by: Optional[str] = Query("publish_date", description="Field to sort by: 'publish_date' or 'weighted_score'"),
    order: Optional[str] = Query("desc", description="Sort order: 'asc' or 'desc'")
):
    """
    Retrieve all papers from the database, along with their evaluation scores.
    Supports pagination (skip, limit) and sorting by publish date or weighted score.
    """
    # Construct the base query joining Publication and PaperScores
    if not start_date:
        # 可以设置一个默认的起始日期，例如一个很早的日期或者当前日期
        start_date = datetime(1970, 1, 1).date()  # 或者 datetime.now().date()        

    if not end_date:
        # 默认截止日期为当前日期
        end_date = datetime.now().date()
    
    publication_list = (
            db.query(Publication)
                .filter(Publication.paper_id != None, Publication.publish_date>=start_date, Publication.publish_date<=end_date)
                .offset(skip).limit(limit).all()  
            ) 
    
    if not publication_list:
        return StandardResponse(
            success= False,
            message='no paper found',
            data={}
        )
    logger.info(f'query table Publication and found {len(publication_list)} records')
    return_data = []
    for publication in publication_list:
        # TODO: 未来会改成，待把作者信息清洗后，就不需要再查询ArxivPaper
        arxiv_paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == publication.paper_id).first()
        item_data = {
            'paper_id':publication.paper_id,
            'publish_date':publication.publish_date,
            'title':publication.title,
            'pdf_url':publication.pdf_url,
            'abstract':publication.abstract,
            'author':arxiv_paper.authors,
            'conclusion':publication.conclusion,
            'traige_qa':publication.triage_qa,
            'scores':publication.scores if publication.scores else "{'review_status':'pending','error_message':'not processed yet'}",
            'weighted_score': publication.scores.weighted_score if publication.scores else 0
        }
        return_data.append(item_data)
    
    # 默认把分数最高的放前面，然后按照日期来排序， TODO: 需要支持更多的方式
    sorted_data = sorted(
        return_data,
        key=lambda x: (x['weighted_score'], x['publish_date']),
        reverse=True
    )
    
    total_count = len(sorted_data)
    return StandardResponse(
        success=True,
        message=f"Retrieved {total_count} papers.",
        data={"papers": sorted_data, "count": total_count}
    )

@router.post("/reviewpaper/{paper_id}", response_model=StandardResponse)
async def paper_review_by_id(db: db_dependency, paper_id: str):
    """
    review a paper, add a comments and score, by paper id
    """
    # 从ArxivPaper 表中根据ID查询，如果该ID已经存在于Publication，且score 表存在该记录，说明我处理过了，直接返回，并跳过
    scores = db.query(PaperScores).filter(PaperScores.paper_id == paper_id).first()

    # 检查是否在 Publication 表中已存在对应的 id
    if scores and scores.paper_id is not None:
        # 该 ID 已存在于 PaperScores 表中，说明已处理过
        rerun= False
        if rerun:
            # TODO 在此处添加您的处理逻辑
            logger.info(f"Paper with ID {paper_id} already exists in PaperScores table. Rerunning...[等待实现]")
            pass
        else:
            # 不需要重新运行，直接返回
            logger.info(f"Paper with ID {paper_id} already exists in PaperScores table. Skipping.") 
        return StandardResponse(
            success=True,
            message=f"Paper with ID {paper_id} already exists in PaperScores table. Skipping.",
            data={"scores": scores}
        )
    else:
        # 该 ID 不存在于 PaperScores 表中，继续处理
        paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == paper_id).first()
        if not paper:
            logger.error(f"Paper with ID {paper_id} not found")
            return StandardResponse(
                success=False,
                message=f"Paper with ID {paper_id} not found"
            )
        arxiv_review = ReviewArxivPaper()
        score = arxiv_review.process(paper)
        if not score:
            logger.error(f"Failed to process paper with ID {paper_id}")
            return StandardResponse(
                success=False,
                message=f"Failed to process paper with ID {paper_id}")
        
        return StandardResponse(
            success=True,
            message=f"Paper with ID {paper_id} processed successfully.",
            data={"scores": score}
        )

@router.post("/reviewpaper_batch", response_model=StandardResponse)
def paper_review_batch_execution(db: db_dependency):
    """
    review a paper, add a comments and score, in a batch way
    """
    unprocessed_papers = (
        db.query(ArxivPaper)
        .outerjoin(PaperScores, ArxivPaper.arxiv_id == PaperScores.paper_id)
        .filter(PaperScores.paper_id.is_(None))
        .all()
    )
    # 检查 unprocessed_papers 是否为空
    if unprocessed_papers:
        logger.info(f"共找到 {len(unprocessed_papers)} 篇未处理的论文")
        arxiv_review = ReviewArxivPaper()
        scores = arxiv_review.process_batch(unprocessed_papers)
        if not scores or len(scores) == 0:
            logger.error("批量处理论文失败")
            return StandardResponse(
                success=False,
                message="批量处理论文失败",
            )
        elif len(scores) != len(unprocessed_papers):
            logger.error(f"批量处理论文成功，但处理的论文数量不匹配: {len(scores)} vs {len(unprocessed_papers)}")
            return StandardResponse(
                success=False,
                message=f"批量处理论文成功，但处理的论文数量不匹配: {len(scores)} vs {len(unprocessed_papers)}",
                data={"scores": scores}
            )
    else:
        logger.info("没有找到未处理的论文")
        return {"message": "没有找到未处理的论文"}
    return StandardResponse(
        success=True,
        message=f"共处理 {len(unprocessed_papers)} 篇论文",
        data={"scores": scores}
    )


# 辅助函数：追加日志信息
def append_log(current_log: str, new_message: str) -> str:
    if current_log:
        return f"{current_log}\n{new_message}"
    return new_message

async def execute_task(task_id: int):
    db = next(get_db())
    try:
        # 获取任务对象
        logger.info(f"开始执行任务: {task_id}")
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"Task not found: {task_id}")
            return
        
        # 创建新的执行记录
        execution = TaskExecution(
            task_id=task_id,
            status=TaskStatus.pending.value,
            start_time=datetime.now(timezone.utc),  # 使用 UTC 时间
            created_at=datetime.now(timezone.utc)   # 显式设置创建时间
        )
        db.add(execution)
        
        func = task_function_mapping.get(task.function_name)
        logger.info(f"获取任务函数: {task.function_name}")
        if not func:
            task.status = TaskStatus.failed.value
            execution.log = append_log(execution.log, f"未找到对应的任务函数: {task.function_name}")
            db.commit()
            return
        
        # 更新任务和执行记录状态为运行中
        task.status = TaskStatus.running.value
        task.start_time = datetime.now()
        execution.status = TaskStatus.running.value
        execution.log = append_log(execution.log, f"任务开始执行: {task.name}")
        execution.log = append_log(execution.log, f"arguments: {task.parameters}")
        db.commit()  # 立即提交状态更新
        
        result = func(task) # 执行任务函数
        
        if result.get("status") == "error":
            raise Exception(result.get("message"))
        execution.log = append_log(execution.log, "任务执行成功")
        # 先直接将结果存储到日志中
        # execution.log = append_log(execution.log, str(result))
        execution.status = TaskStatus.completed.value
        execution.end_time = datetime.now()

        # 更新任务状态
        task.status = TaskStatus.completed.value
        task.end_time = datetime.now()
        logger.info(f"任务执行完成: {task.name}")
        
        logger.info(f"开始存储数据到数据库")
        execution.log = append_log(execution.log, f"开始存数据到数据库")
        if result.get("data") and result.get("data").get("papers"):
            papers_count = 0
            duplicate_count = 0
            total_count = len(result.get("data").get("papers"))
            logger.info(f"共找到 {total_count} 篇论文")
            for paper_data in result.get("data").get("papers"):
                # 检查数据库中是否已存在相同 arxiv_id 的论文
                logger.info(f"处理论文: {paper_data.get('arxiv_id')}")
                existing_paper = db.query(ArxivPaper).filter(ArxivPaper.arxiv_id == paper_data.get("arxiv_id")).first()
                if existing_paper:
                    # 如果存在，可以选择更新或跳过，这里示例为跳过
                    logger.info(f"跳过重复论文: {paper_data.get('arxiv_id')}")
                    execution.log = append_log(execution.log, f"跳过重复论文: {paper_data.get('arxiv_id')}")
                    duplicate_count += 1
                    continue
                else:
                    # 创建新论文记录
                    logger.info(f"保存论文: {paper_data.get('arxiv_id')}")
                    execution.log = append_log(execution.log, f"保存论文: {paper_data.get('arxiv_id')}")
                    new_paper = ArxivPaper(
                        arxiv_id=paper_data.get("arxiv_id"),
                        title=paper_data.get("title"),
                        pdf_url=paper_data.get("pdf_url"),
                        published=paper_data.get("published"),
                        summary=paper_data.get("summary"),
                        authors=paper_data.get("authors"),
                        primery_category=paper_data.get("primary_category"),
                        categories=paper_data.get("categories"),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(new_paper)
                    papers_count += 1
            
            db.commit()  # 提交所有更改
            execution.log = append_log(
                execution.log, 
                f"成功保存 {papers_count} 篇论文到数据库, 跳过 {duplicate_count} 篇重复论文"
            )
            logger.info(f"成功保存 {papers_count} 篇论文到数据库, 跳过 {duplicate_count} 篇重复论文")
        else:
            logger.info("未找到需要保存的论文数据")
            execution.log = append_log(execution.log, "未找到需要保存的论文数据")

    except Exception as e:
        # 更新执行记录为失败
        if execution:  # 确保 execution 存在
            execution.status = TaskStatus.failed.value
            execution.end_time = datetime.now()
            execution.log = append_log(execution.log, str(e))
        logger.error(f"Error executing task {task_id}: {str(e)}")
        
        # 更新任务状态
        task.status = TaskStatus.failed.value
    finally:
        task.last_run_time = datetime.now()
        # 如果任务为周期性任务，更新 next_run_time，并重置状态为 pending 以便下次执行
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
    Backend task function to crawl papers from arxiv
    
    Args:
        query (str): The affiliation name to search for
        start (int): Starting index for results
        max_results (int): Maximum number of results to return
    """
    try:
        crawler = ArxivCrawler()
        logger.info("爬取 arxiv 数据, task_id=%s", task.id)
        # 从任务参数中获取查询参数
        url = task.parameters.get("url", "")
        if not url:
            raise ValueError("URL is required")
        # 其他参数
        args = ArxivApiArgs(
            search_query=task.parameters.get("query", ""),
            start=task.parameters.get("start", 0),
            max_results=task.parameters.get("max_results", 10),
            sortBy=task.parameters.get("sortBy", "submittedDate"),   # 可选参数，可以省略
            sortOrder=task.parameters.get("sortOrder", "descending")     # 可选参数，可以省略
        )
        logger.info(f"爬取 arxiv 数据 url={url}, args={args}")
        # 设置查询参数
        results = crawler.get_api_response(url, args)
        if not results:
            raise ValueError("No results found")
        return {
            "status": "success",
            "message": "Crawling completed successfully",
            "data": results
        }
    except Exception as e:
        logger.error(f"Error crawling arxiv: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

# 构建函数映射字典，键为任务名称，值为对应的函数对象
task_function_mapping = {
    'crawl_arxiv': crawl_arxiv,
    # 可以在这里添加更多的任务函数
}


