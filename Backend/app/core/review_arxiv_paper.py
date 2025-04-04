
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
import logging
import math
import re
import time
from typing import Dict, List

from fastapi import Path
import fitz
from openai import OpenAI
import requests
from app.database import SessionLocal
from models.tasks import ArxivPaper, PaperScores, Publication, SOTAContext

# Configure the logging format to include the timestamp
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Set the logging level as needed
    datefmt='%Y-%m-%d %H:%M:%S'  # Customize the timestamp format
)

# Create a logger instance
logger = logging.getLogger(__name__)

class BaseAssistant:
    def __init__(self, config: dict):
        self.name = config.get('name')
        self.model_name = config.get('model_name')
        self.prompt = config.get('prompt')
        self.instruction = config.get('instruction')
        self.client = OpenAI()  # 在初始化时创建一个共享的客户端实例
        
    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    def do_work(self, publication: Publication, context:dict) -> dict:
        return self._get_response(publication=publication, prompt=self.prompt)
    
    def ask_question(self, publication: Publication,prompt:str) -> dict:
        # 追问更多问题
        return self._get_response(publication=publication, prompt=prompt)
    
    def _get_response(self, publication: Publication,prompt:str) -> dict:
        try:
            # 调用 OpenAI 接口
            response = self.client.responses.create(
                model=self.model_name,
                instructions=self.instruction,
                input=prompt,
                max_output_tokens=10000   #TODO: 这里可以根据实际需要调整,开发阶段，限制长度
            )
            # 解析并返回结果
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {e}")
            raise e
    
    def _load_domain_sota_knowledge(self, publication:Publication) -> str:
        if publication.keywords:
            keywords = publication.keywords
        elif publication.title:
            keywords = "I dont have keywords, but I have the title: " + publication.title
        # 让AI来总结文章的研究方向/关键技术，这个不总是等于关键字, 应该要比关键字更加具体。 比如“kv cache的压缩”
        key_topics = self.ai_assisstant(publication=publication, context=keywords, prompt=self.prompt)
        if keywords:
            db = next(self.get_db())
            knowledge = """Remember, you are the best expector in this domain,and here is some short summery of the backgroud knowledge which can help do the deep anaylsis:"""
            sota_context_list =[]
            # 根据top 3 的关键字（节约上下文），先从数据库中获取相关的知识
            for keyword in keywords.split(',')[:3]:
                sota_context = db.query(SOTAContext).filter(SOTAContext.keyword == keyword).first()
                if sota_context:
                    sota_context_list.append(sota_context.research_context)
            if sota_context_list:
                sota_str = '\n\n'.join(sota_context_list)
                return f'Remember, you are the Best Expert \
            in this domain, and here is some short summery of \
            the backgroud knowledge which can help do the deep anaylsis:{sota_str}'
        else:
            return 'Remember, you are the best expector in this domain. \
                I can not provide enough backgroud knowledge context to you, \
                please try your best based on your memory.\n'
    
    def _parse_response(self, response) -> dict:
        # 解析 OpenAI 的响应并提取评分结果
        # TODO: 实际上还可以考虑增强一些逻辑，处理异常情况，提高容错能力。比如ai 的分数是不是在 0-10 之间？
        if not response or not hasattr(response, 'output_text'):
            raise ValueError("Invalid response from OpenAI API.")
        return response.output_text

class TopicSummaryAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get('name')
        self.model_name = config.get('model_name')
        self.prompt = config.get('prompt')
        self.instruction = config.get('instruction')
    
    def do_work(self, publication, context):
        if publication.research_topics:
            # 如果论文已经包含研究课题,then 直接使用
            return {"keywords": publication.keywords, 
                    "research_topics": publication.research_topics}
            
        if publication.keywords:
            keywords = publication.keywords
        elif publication.title:
            keywords = "I dont have keywords, but I have the title: " + publication.title
        else:
            keywords = "I dont have keywords, and I dont have title. Please try your best."
        prompt = self.prompt.format(
            title=publication.title,
            keyword_list=keywords,
            abstract=publication.abstract,
            conclusion=publication.conclusion)
            
        return self._get_response(publication=publication, prompt=prompt)
      
class TraigeAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get('name')
        self.model_name = config.get('model_name')
        self.prompt = config.get('prompt')
        self.instruction = config.get('instruction')
    
    def do_work(self, publication, context):
        """"
        论文标题：{title}
        关键字：{keywords}
        摘要：{abstract}
        结论：{conclusion}
        文章全文：{full_text}
        为了帮助你更好地回答问题，以下是一些该领域的前沿研究成果（SOTA）：
        {sota_context}  
        """
        # get the sota context
        sota_context = self._load_domain_sota_knowledge(publication)
        # build the prompt
        prompt = self.prompt.format(
            title=publication.title,
            keywords=publication.research_topics,
            abstract=publication.abstract,
            conclusion=publication.conclusion,
            full_text=publication.content_raw_text[:10000], # TODO测试阶段，限制长度
            sota_context=sota_context
            )
        return self._get_response(publication=publication, prompt=prompt)
    
class DomainExpertReviewAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get('name')
        self.model_name = config.get('model_name')
        self.prompt = config.get('prompt')
        self.instruction = config.get('instruction')
    
    def do_work(self, publication, context):
        # update the instruction, TODO： 感觉应该有更好的地方来处理这个逻辑
        if self.name == AIAssistantType.REVIEWER_GENERAL:
            self.instruction = self.instruction.format(domain=publication.research_topics)
        else:
            # 如果是domain的专家，请专家自己来加载他的专业领域知识, TODO: 带考虑，现在直接pass
            pass
        # build the prompt
        """
            **标题**：{title}
            **关键字**：{keywords}
            **摘要**：{abstract}
            **结论**：{conclusion}
            **关于本文的关键信息摘要或者问答**：{traige_summary}
        """
        if not context:
            context = "I dont have enough context, please try your best."
            
        prompt = self.prompt.format(
            title=publication.title,
            keywords=publication.research_topics,
            abstract=publication.abstract,
            conclusion=publication.conclusion,
            traige_summary=context
        )
        return self._get_response(publication=publication, prompt=prompt)

class AIAssistantType(Enum):
    PAPER_TRIAGE = "paper_triage"
    TOPIC_SUMMARY = "topic_summary"
    REVIEWER_GENERAL = "reviewer_general"
    DOMAIN_REVIEWER_ALGORITHM = "domain_reviewer_algorithm"
    DOMAIN_REVIEWER_ARCHITECT = "domain_reviewer_architect"
    DOMAIN_REVIEWER_CLUSTER = "domain_reviewer_cluster"
    DOMAIN_REVIEWER_CHIP = "domain_reviewer_chip"
    DOMAIN_REVIEWER_NETWORK = "domain_reviewer_network"
    # xxx_domain 可以注入更多定制化的专家

class PaperReviewConfig:
    SECTION_TITLES = {
        "abstract": {"abstract"},
        "introduction": {"introduction", "background", "preliminaries", "preliminary"},
        "related_work": {"related work", "prior work", "literature review", "related studies"},
        "methodology": {"methodology", "methods", "method", "approach", "proposed method", 
                        "model", "architecture", "framework", "algorithm", "system design"},
        "experiment": {"experiment", "experiments", "experimental setup", "experiment setup",
                    "setup", "implementation details", "evaluation", "evaluation setup"},
        "ablation":{"ablation","ablation study"},
        "results": {"results", "performance", "findings", "observations", "empirical results"},
        "discussion": {"discussion", "analysis", "interpretation"},
        "summary":{"summary"},
        "conclusion": {"conclusion", "final remarks", "closing remarks"},
        "limitations":{"limitations"},
        "acknowledgments": {"acknowledgments", "acknowledgements", "funding", "author contributions"},
        "references": {"references", "bibliography", "cited works"},
        "appendix": {"appendix", "supplementary material", "supplementary", "additional materials"}
    }

    # 论文拆分参数
    MAX_LINE_PER_CHUNK = 25  # 每个 chunk 最大行数
    OVERLAP_LINES = 5  # 上下文重叠行数
    REFERENCE_BLOCK_SIZE = 8  # 参考文献块大小（5~10行）
    
    GPT_MODEL_NAME = "gpt-4o-mini"

    ai_assistants_config = {
        AIAssistantType.TOPIC_SUMMARY: {
            "name": "topic_summary",
            "model_name": "gpt-4o-mini",
            'instruction': '作为一名专业的学术论文分析专家，你的任务是阅读并分析提供的论文信息，包括标题、关键字（如有）、摘要和结论。你的目标是从中提取出以下内容：\
                            1. 关键字：总结论文主题的核心术语。\
                            2. 研究课题：提炼论文研究的前三大具体课题或方向，这些课题应比关键字更具体和明确。例如，关键字可能是“缓存”，但具体的研究课题可能是“键值缓存的压缩方法”。\
                            请将上述信息以JSON格式返回。',
            'prompt': """请阅读以下论文信息:
                    标题：{title}
                    关键字：{keyword_list}
                    摘要：{abstract}
                    结论：{conclusion}
                    基于上述信息,请提取并列出该论文研究的Top 3个具体课题或研究方向。
                    要求： 
                    1. 请保持技术专业术语，不要求翻译为中文
                    2. 内容不要太长简明扼要。
                    根据上述信息,提取并返回以下内容的JSON对象,不要添加额外的任何注释,要保证Json格式正确:
                    {
                        "keywords": ["关键词1", "关键词2", "关键词3", ...],
                        "research_topics": ["研究课题1", "研究课题2", "研究课题3"]
                    }""",
            
        },
        AIAssistantType.PAPER_TRIAGE: {
            'name': "paper_triage",
            'model_name': "gpt-4o-mini",
            'instruction': """你是一位资深的学术论文审稿专家，熟悉学术界和工业界的前沿研究动态。我将为你提供一篇论文的核心信息，包括标题、关键字、摘要、结论和作者信息等。
                        请你基于这些内容，系统性地分析并回答以下六个问题：
                        1. 该论文试图解决的核心问题是什么？
                        2. 该论文的主要技术贡献是什么？
                        3. 论文提出的方案或建议中，有哪些创新点值得关注？
                        4. 该论文是否与当前领域内的 SOTA（state-of-the-art）研究成果进行了对比？如果有，对比结论是什么？
                        5. 该论文的作者及其所属机构分别是谁？请尽量完整列出。
                        6. 请评估作者和所属机构在学术界或工业界的影响力，例如：是否为知名大学、实验室或工业研究机构，是否有广泛引用或业界应用。
                        请确保回答准确、专业，且符合论文内容。
                            """,
            'prompt': """请根据以下论文信息，完整、准确地回答对应的问题，并使用符合规范的 JSON 格式返回结果：
                        论文标题：{title}
                        关键字：{keywords}
                        摘要：{abstract}
                        结论：{conclusion}
                        文章全文：{full_text}
                        为了帮助你更好地回答问题，以下是一些该领域的前沿研究成果（SOTA）：
                        {sota_context}
                        
                        要求：
                        - 用 JSON 格式严格返回答案，不要添加多余的文字或注释。
                        - 请将每个问题的答案替换到以下 JSON 模板中的相应位置：
                        - 保证 JSON 可被机器正确解析，确保语法无误。

                        返回格式示例：
                        {
                        "core_problem": "请填写该论文试图解决的核心问题。",
                        "technical_contributions": "请填写该论文的主要技术贡献。",
                        "innovations_and_proposals": [
                            "请列举该论文提出的创新点或建议1",
                            "请列举该论文提出的创新点或建议2"
                        ],
                        "sota_comparison": "请填写论文是否与SOTA进行了对比，以及对比的结论。",
                        "authors_and_affiliations": {
                            "authors": ["作者1", "作者2"],
                            "institutions": ["机构1", "机构2"]
                        },
                        "influence_assessment": "请评估作者和机构的学术或产业影响力。"
                        }""",
        },
        AIAssistantType.REVIEWER_GENERAL: {
            'name': "reviewer_general",
            'model_name': "gpt-4o-mini",
            'instruction': """作为一名在{domain}的资深专家，您将收到一篇论文的核心信息。请根据以下五个维度对该论文进行评分，评分范围为1.0到10.0，其中10.0分代表最佳表现(分数可以有小数点后2两位)。请严格依据提供的论文内容和背景信息，确保评估的公平性和公正性。
                        1. **技术创新性（Technical Innovation）**：评估该方法相对于已有方案的新颖程度。例如，判断论文是否引入了前所未有的新机制，或将传统必要组件替换为全新架构。若该工作开辟了新方向，引发社区关注新的研究范式，则应给予高分（8分以上）。
                        2. **性能提升幅度（Performance Improvement）**：检查其在公认基准数据集上的实验结果，并与之前发表的最佳结果进行比较。若主要指标有显著提升，可判定为高分。需关注提升是否在多个任务或数据集上复现，体现方法的普适性和强大性能增益。
                        3. **理论或工程简洁性（Theoretical/Engineering Simplicity & Efficiency）**：评估方法是否降低了计算复杂度或工程难度。例如，算法的时间复杂度是否减少，模型参数或内存占用是否降低，训练所需算力或时间是否缩短。若在保持或提高性能的同时，简化了模型结构或提高了训练推理效率，应给予高分。
                        4. **可复用性与影响力（Reusability & Impact）**：考察该工作的通用性和影响力。若论文提供了易于迁移到其他任务的模型结构或算法，并被广泛采用，说明其可复用性和影响力高。反之，若方法过于定制或复杂，鲜有他人采用，则此维度得分较低。
                        5. **作者与机构权威度（Author & Institutional Authority）**：查阅作者背景和机构信息，了解其以往研究成果。若作者来自顶级研究单位或曾发表过有影响力的相关工作，且机构拥有强大的研究传统，则权威度评分应相应提高。
                        在完成上述评分后，请给出是否推荐阅读该论文的建议（"yes"或"no"），并说明理由。若论文主要是信息汇总，且未提供额外价值信息，可给予低分，并明确表示不推荐。
                        最后，请评估你对该论文的信心程度，范围为0.0到1.0，0.0表示完全不确定，1.0表示非常确定。请根据你对论文内容的理解和分析，给出一个合理的信心值。
                        请将最终结果以以下JSON格式输出，确保格式严格正确，不要添加额外信息：
                        {
                            "score": [
                                {
                                "innovation": 7,
                                "reason": "The paper systematically reviews and categorizes ….."
                                },
                                {
                                "performance": 5,
                                "reason": "As a survey paper, it does not present new experimental results ….."
                                },
                                {
                                "simplicity": 6,
                                "reason": "The paper discusses the computational characteristics and potential ….."
                                },
                                {
                                "reusability": 8,
                                "reason": "By categorizing ….."
                                },
                                {
                                "authority": 7,
                                "reason": " a reputable institution known for its contributions to …."
                                }
                            ],
                            "recommend": "yes",
                            "reason": "The paper offers a comprehensive overview of ….."
                            "who_should_read": "beginner… "
                            "confidence": 0.85
                        }""",
            'prompt': """请根据以下论文信息，按照上述指令进行评估：
                        **标题**：{title}
                        **关键字**：{keywords}
                        **摘要**：{abstract}
                        **结论**：{conclusion}
                        **关于本文的关键信息摘要或者问答**：{traige_summary}
                        请严格按照指令中的要求，完成对该论文的评估，并以指定的JSON格式返回结果。""",
            
        },
        AIAssistantType.DOMAIN_REVIEWER_ALGORITHM: {
            'instruction': """你是一位在<计算机软件和算法研究领域>的资深专家，拥有广泛的研究和审稿经验。你收到了一篇论文的核心信息，以及通用 AI Reviewer 给出的初步评分结果，供你参考。
                            请按照以下步骤进行：
                            1. **相关性判断**：首先判断该论文是否与你的专业领域 <计算机软件和算法研究领域> 有密切关联。
                            - 如果判断为“无关”，请不要修改已有评分，直接返回原始评分结果，并补充上你的 confidence 值（例如 0.4），说明该论文与您的领域无关。
                            2. **评分复核与修正**：
                            - 如果该论文与你的领域密切相关，请仔细审阅通用 reviewer 的评分，基于你的专业理解，进行合理的校对或小幅修改。
                            - 避免大幅调整，除非你有充分的专业理由。若有修改，请简要说明原因。
                            - 评分维度包括：
                                - 创新性（innovation）
                                - 性能提升（performance）
                                - 简洁性与效率（simplicity）
                                - 可复用性与影响力（reusability）
                                - 作者与机构权威度（authority）

                            3. **推荐与信心度**：
                            - 保留或修改推荐意见（recommend），以及目标读者建议（who_should_read）。
                            - 最后，请给出你对整体评估的信心度（confidence），范围是 0 到 1，例如 0.85 表示较高信心。

                            ⚠️ 注意：
                            - 严格按照要求的 JSON 格式输出结果，确保格式正确且可被机器读取。
                            - 除 JSON 以外，不要添加多余的说明文字或注释。""",
            'prompt': """请基于以下论文信息和已有的通用 reviewer 的评分，完成你的评审任务。
                        【论文信息】
                        标题：{title}
                        关键字：{keywords}
                        摘要：{abstract}
                        结论：{conclusion}
                        关于本文的关键信息摘要或者问答：{traige_summary}
                        【已有评分参考】
                        {previous_review_json}
                        请按照指令，判断领域相关性，并复核或确认评分。请严格按照以下格式返回结果：
                        {
                            "score": [
                                {
                                "innovation": 7,
                                "reason": "The paper systematically reviews and categorizes ….."
                                },
                                {
                                "performance": 5,
                                "reason": "As a survey paper, it does not present new experimental results ….."
                                },
                                {
                                "simplicity": 6,
                                "reason": "The paper discusses the computational characteristics and potential ….."
                                },
                                {
                                "reusability": 8,
                                "reason": "By categorizing ….."
                                },
                                {
                                "authority": 7,
                                "reason": " a reputable institution known for its contributions to …."
                                }
                            ],
                            "recommend": "yes",
                            "reason": "The paper offers a comprehensive overview of ….."
                            "who_should_read": "beginner… "
                            "confidence": 0.85
                        }""",
            
        },
        # TODO: 其他领域的评审助手配置
    }

class ReviewArxivPaper:
    '''
    1. 初始化 OpenAI 客户端，会多次发送请求
    2. 对单一论文，首先检查论文 PDF 是否被下载，如果没有，就开启下载
    3. 对于下载好的论文，开始解析 PDF，转为文本，针对文本片段开始调用 OpenAI 的接口做分析
    4. 定义 5 个不同的 AI 助手，基于文本，对论文开始打分
    '''

    def __init__(self):
        '''
        初始化 OpenAI 客户端
        '''
        self.client = OpenAI()

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    def process(self, paper: 'ArxivPaper'):
        '''
        处理单篇论文
        '''
        if not self._is_pdf_downloaded(paper):
            pdf_path = self._download_pdf(paper)
        # 1. 简单处理，去掉空行
        text = self._parse_pdf_to_text(pdf_path)
        text_lines = [line.strip() for line in text.split("\n") if line.strip()]
        # 2. 论文的一些典型识别标题
        title_indices = self._detect_section_titles(text_lines)
        # 3. 按标题拆分
        section_chunks = self._split_to_chunks_by_title(text_lines, title_indices)
        # 4. 选出重点内容
        abstract_text = section_chunks.get('abstract', '')
        conclusion_text = section_chunks.get('conclusion', '')
        references_text = section_chunks.get('references', '')
        full_text_lines=[]
        for key in title_indices:
            print(key)
            full_text_lines.append('\n'.join(section_chunks.get(key)))
            if key.strip().lower() == 'conclusion' or key.strip().lower() == 'references':
                break
        main_context = '\n'.join(full_text_lines)
        
        # 新建一个publication
        publication = Publication(
            id = paper.arxiv_id,
            instance_id=0, # 默认关联到一个非会议
            title=paper.title,
            year= datetime.strptime(paper.published, '%Y-%m-%d').strftime('%Y'),
            publish_date=paper.published,
            tldr='',
            abstract=paper.summary if paper.summary else abstract_text,
            conclusion= conclusion_text,
            content_raw_text= main_context,
            reference_raw_text=references_text,
            pdf_path= pdf_path,
            citation_count=0,
            award='',
            doi='',
            url='',
            pdf_url=paper.pdf_url,
            attachment_url=''
        )
        # 先保存到数据库
        db = next(self.get_db())
        db.add(publication)
        db.commit()
        # 然后交给评审打分
        db.refresh(publication)
        scores =self._review_paper_with_ai_experts(publication)
        db.add(scores)
        db.commit()

    def process_batch(self, paper_list: List['ArxivPaper']):
        '''
        批量处理论文
        '''
        # TODO: 一次处理两篇论文，调试完成后删除
        paper_list = paper_list[:2]
        
        max_threads = 4  # 根据您的系统和任务需求调整线程数
        with ThreadPoolExecutor(max_threads) as executor:
            # 提交所有任务
            future_to_paper = {executor.submit(self.process, paper): paper for paper in paper_list}
            # 等待所有任务完成
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    future.result()  # 获取线程执行结果
                except Exception as exc:
                    logger(f'{paper} 处理时发生异常: {exc}')

    def _detect_section_titles(lines):
        """检测标题行，返回标题索引"""
        title_indices = {}
        section_num = 0 # 对于 summary、limitation 这类标题，可能在多个位置出现，需要全部保留。加一个编码，保证独立
        for i, line in enumerate(lines):
            clean_line = re.sub(r"[^a-zA-Z\s]", "", line).strip().lower()
            for section, keywords in PaperReviewConfig.SECTION_TITLES.items():
                if any(re.match(rf"^\s*(\d+([\.\-）]\d+)*[\.\-）]*\s*)?{re.escape(kw)}\s*$", clean_line, re.IGNORECASE) for kw in keywords):
                    if (section in title_indices):
                        title_indices[section+"_"+str(section_num)] = i
                        section_num += 1
                    else:
                        title_indices[section] = i
                    break
        return title_indices
    
    def _split_to_chunks_by_title(lines, title_indices):
        """按照标题行分块"""
        chunks = defaultdict(list)
        sorted_sections = sorted(title_indices.items(), key=lambda x: x[1])  # 按出现顺序排序

        for idx, (section, start_idx) in enumerate(sorted_sections):
            end_idx = sorted_sections[idx + 1][1] if idx + 1 < len(sorted_sections) else len(lines)
            chunks[section] = lines[start_idx:end_idx]
        
        return chunks
    
    def _get_pdf_path(paper):
        """
        根据论文信息生成对应的 PDF 存储路径。
        假设 paper.date 是 'YYYY-MM-DD' 格式的字符串，paper.id 是论文的唯一标识符。
        """
        paper_date = datetime.strptime(paper.published, '%Y-%m-%d')
        year = paper_date.strftime('%Y')
        month = paper_date.strftime('%m')
        
        # 获取当前文件 core.py 的绝对路径
        current_file = Path(__file__).resolve()

        # 获取项目根目录 backend/
        project_root = current_file.parents[2]
        # 构建 pdf 存储目录
        pdf_dir = project_root / 'data' / 'pdf' / year / month
        pdf_path = pdf_dir / f"{paper.id}.pdf"
        
        # 如果目录不存在，则创建
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        return pdf_dir, pdf_path

    def _is_pdf_downloaded(self, paper: 'ArxivPaper') -> bool:
        '''
        检查论文的 PDF 是否已下载
        '''
        # 实现检查逻辑
        pdf_dir, pdf_path = self._get_pdf_path(paper)
        return pdf_path.is_file()

    def _download_pdf(self, paper: 'ArxivPaper') ->str:
        """
        下载论文的 PDF 并保存到指定路径。
        """
        _, pdf_path = self._get_pdf_path(paper)
        
        response = requests.get(paper.pdf_url)
        if response.status_code == 200:
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception(f"无法下载 PDF,HTTP 状态码：{response.status_code}")
        return pdf_path

    def _parse_pdf_to_text(self, pdf_path) -> str:
        '''
        解析 PDF 并将其转换为文本
        '''
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            # print(page.number, page.get_text()[:20])
            text += page.get_text()
        return text

    def _get_key_research_topics(self, publication: Publication) -> str:
        '''
        从论文中提取关键研究方向
        '''
        # 实现提取逻辑
    def _get_triage_qa(self, publication: Publication) -> str:
        '''
        从论文中提取关键问题
        '''
        # 实现提取逻辑
    def _review_paper_with_ai_experts(self, publication: Publication) -> PaperScores:
        '''
        使用 OpenAI 接口分析文本，并根据不同标准进行评分
        '''
        try:
            # 0. 先让论文总结研究的关键方向, 
            topic_summary_config = PaperReviewConfig.ai_assistants_config[AIAssistantType.TOPIC_SUMMARY]
            topic_summary_assistant = TopicSummaryAssistant(topic_summary_config)
            topic_result = topic_summary_assistant.do_work(publication, context="")
            if not topic_result:
                if not publication.keywords:
                    publication.keywords = topic_result.get('keywords', '')
                if not publication.research_topics:
                    publication.research_topics = topic_result.get('research_topics', '')
            # 1. 让AI总结论文的几个关键问题, 以及答案，辅助推理
            triage_assistant_config = PaperReviewConfig.ai_assistants_config[AIAssistantType.PAPER_TRIAGE]
            triage_assistant = TraigeAssistant(triage_assistant_config)
            context = ''
            if publication.research_topics:
                context = f"Here are some key research topics: {publication.research_topics}"
            triage_qa_result = triage_assistant.do_work(publication, context)
            # save triage result
            if triage_qa_result:
                publication.triage_qa = triage_qa_result
            # 
            # 2. 让AI 根据初步的信息来打分，自动检索相关核心问题的state of the art 研究成果作为补充判断
            reviwer_general = PaperReviewConfig.ai_assistants_config[AIAssistantType.REVIEWER_GENERAL]
            reviewer_general_assistant = DomainExpertReviewAssistant(reviwer_general)
            init_score = reviewer_general_assistant.do_work(publication, context=triage_qa_result)
            if not init_score:
                raise ValueError("Invalid response from OpenAI API.")
            # 2.1. 处理初步评分结果
            score = PaperScores(
                paper_id= publication.id,
                title=publication.title,
                innovation_score=init_score.get('innovation_score', 0.0),
                innovation_reason=init_score.get('innovation_reason', 'N/A'),
                performance_score=init_score.get('performance_score', 0.0),
                performance_reason=init_score.get('performance_reason', 'N/A'),
                simplicity_score=init_score.get('simplicity_score', 0.0),
                simplicity_reason=init_score.get('simplicity_reason', 'N/A'),
                reusability_score=init_score.get('simplicity_score', 0.0),
                reusability_reason=init_score.get('simplicity_reason', 'N/A'),
                authority_score=init_score.get('authority_score', 0.0),
                authority_reason=init_score.get('authority_reason', 'N/A'),
                weighted_score= 0.0,
                recommend=init_score.get('recommend', False),
                recommend_reason=init_score.get('recommend_reason', ''),
                who_should_read=init_score.get('who_should_read', ''),
                confidence_score=init_score.get('confidence', 0.0),
                ai_reviewer= reviewer_general_assistant.name,
                review_status="success",
                error_message="",
                log=f"AI reviewer {reviewer_general_assistant.name} reviewed the paper and provided initial score."
            )
            # 3: 遍历领域专家，对打分进行核查和修正
            domain_reviwers = self._load_domain_review_assistants()
            for expert_name, expert_assistant in domain_reviwers.items():
                logger.info(f"Processing paper {publication.id} with expert {expert_name}")
                expert_score = expert_assistant.do_work(publication, context=triage_qa_result)
                if expert_score and expert_score.get("confidence"):
                    # <0.75, 认为该专家跟跟此论文无关。 否则判断和合并专家的结果
                    if expert_score.get('confidence') > score.confidence_score:
                        score.innovation_score = expert_score.get('innovation_score')
                        score.innovation_reason = expert_score.get('innovation_reason')
                        score.performance_score = expert_score.get('performance_score')
                        score.performance_reason = expert_score.get('performance_reason')
                        score.simplicity_score = expert_score.get('simplicity_score')
                        score.simplicity_reason = expert_score.get('simplicity_reason')
                        score.reusability_score = expert_score.get('simplicity_score')
                        score.reusability_reason = expert_score.get('simplicity_reason')
                        score.authority_score = expert_score.get('authority_score')
                        score.authority_reason = expert_score.get('authority_reason')
                        score.recommend = expert_score.get('recommend')
                        score.recommend_reason = expert_score.get('recommend_reason')
                        score.who_should_read = expert_score.get('who_should_read')
                        score.confidence_score = expert_score.get('confidence')
                        score.ai_reviewer = ','.join(score.ai_reviewer, expert_assistant.name)
                        score.review_status = "success"
                        score.error_message = ""
                        score.log ='\n'.join(score.log, f"Expert {expert_name} reviewed the paper and provided update: {score.get_review_status()}")
                    else:
                        score.log = '\n'.join(score.log,f"Expert {expert_name} reviewed the paper, but confidence is low.")
                else:
                    score.log = '\n'.join(score.log, f"Expert {expert_name} reviewed the paper but no valid score provided.")
            # 4. 计算综合得分
            score.weighted_score = round(0.35*score.innovation_score + 
                                         0.25*score.performance_score + 
                                        0.15*score.simplicity_score + 
                                        0.15*score.reusability_score + 
                                        0.1*score.authority_score,
                                        2)
            score.log = '\n'.join(score.log, f"Final score calculated: {score.weighted_score}")
            return score       
        except Exception as e:
            logger.error(f"Error processing paper {publication.id}: {e}")
            raise e
    
    def _load_domain_review_assistants(self) -> Dict[AIAssistantType, DomainExpertReviewAssistant]:
        assistants = {}
        for assistant_type, config in PaperReviewConfig.ai_assistants_config.items():
            assistants[assistant_type] = DomainExpertReviewAssistant(config)
        return assistants
