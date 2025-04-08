from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import date, datetime
from enum import Enum
import json
import logging
import math
import os
from pathlib import Path
import re
from string import Template
import sys
import time
from typing import Dict, List

import fitz
from openai import OpenAI, Timeout
import requests
from dotenv import load_dotenv
from config import get_data_storage_dir
from database import SessionLocal
from models.tasks import ArxivPaper, PaperScores, Publication, SOTAContext
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(funcName)s[%(lineno)d] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)
# Create logger for this module
logger = logging.getLogger(__name__)


class InMemoryCacheDevOnly:
    def __init__(self):
        self.cache = {}

    def get(self, prompt: str):
        """
        Retrieve the cached response for the given prompt.
        Returns the JSON response if found, or None if not cached.
        """
        return self.cache.get(prompt)

    def set(self, prompt: str, response: dict):
        """
        Cache the JSON response for the given prompt.
        """
        self.cache[prompt] = response


cache = InMemoryCacheDevOnly()


class BaseAssistant:
    def __init__(self, config: dict):
        self.name = config.get("name")
        self.model_name = config.get("model_name")
        self.prompt = config.get("prompt")
        self.instruction = config.get("instruction")
        # Get API key from environment variables (loaded from .env file)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)

    def _get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def do_work(self, publication: Publication, context: dict) -> dict:
        return self._get_response(publication=publication, prompt=self.prompt)

    def ask_question(self, publication: Publication, prompt: str) -> dict:
        # 追问更多问题
        return self._get_response(publication=publication, prompt=prompt)

    def _get_response(self, publication: Publication, prompt: str) -> dict:
        max_retries = 2  # 允许重试2次
        cached_response = cache.get(prompt)
        if cached_response:
            logger.info(f"!!biggo!!Cached response return: {cached_response}")
            return cached_response

        for attempt in range(max_retries + 1):
            try:
                # 调用 OpenAI 接口
                response = self.client.responses.create(
                    model=self.model_name,
                    instructions=self.instruction,
                    input=prompt,
                    max_output_tokens=10000,  # TODO: 这里可以根据实际需要调整,开发阶段，限制长度
                )
                # 解析并返回结果
                result = self._parse_response(response)
                # TODO: 优化它
                cache.set(prompt=prompt, response=result)
                return result
            except ValueError as ve:
                logger.error(
                    f"Recived an invalid response from LLM API call\n Response:{response} \n and the errors are:\n {ve}"
                )
                logger.info(f"Retrying {attempt + 1}...")
            except Exception as e:
                logger.error(
                    f"Recived an invalid response from LLM API call\n Response:{response} \n and the errors are:\n {ve}"
                )
        # failed retry:
        logger.error(f"Attempt {attempt + 1} failed. Exit with error!!!")
        return None

    def _load_domain_sota_knowledge(self, publication: Publication) -> str:
        if publication.research_topics:
            keywords = publication.research_topics
        elif publication.keywords:
            keywords = publication.keywords
        else:
            keywords = (
                "I dont have keywords, but I have the title: " + publication.title
            )
        # 让AI来总结文章的研究方向/关键技术，这个不总是等于关键字, 应该要比关键字更加具体。 比如“kv cache的压缩”
        # set default value:
        sota_result = f"Remember, you are the best expector in this domain. \
                I can not provide enough backgroud knowledge context to you, \
                please try your best based on your memory.\n"
        if keywords:
            db = next(self._get_db())
            sota_context_list = []
            # 根据top 3 的关键字（节约上下文），先从数据库中获取相关的知识
            for keyword in keywords[:3]:
                sota_context = (
                    db.query(SOTAContext).filter(SOTAContext.keyword == keyword).first()
                )
                if sota_context and sota_context.research_context:
                    sota_context_list.append(sota_context.research_context)
            if sota_context_list:
                sota_str = "\n".join(sota_context_list)
                sota_result = f"Remember, you are the Best Expert \
            in this domain, and here is some short summery of \
            the backgroud knowledge,they are state-of-the-art knowledges, \
                which can help do the deep anaylsis:{sota_str}"

        logger.info(f"Load domain SOTA knowledge: {sota_result}")
        return sota_result

    def _parse_response(self, response) -> dict:
        # 解析 OpenAI 的响应并提取评分结果, 默认返回结果都是json 格式，除去```json
        if not response or not hasattr(response, "output_text"):
            raise ValueError("Invalid response from OpenAI API.")
        # convert it to json date type
        try:
            # Remove optional 'json' identifier after the opening triple backticks
            response_text = response.output_text
            cleaned_result = re.sub(r"^```json\s*", "", response_text)
            # Remove closing triple backticks
            cleaned_result = re.sub(r"```$", "", cleaned_result)
            # TODO: 实际上还可以考虑增强一些逻辑，处理异常情况，提高容错能力。比如ai 的分数是不是在 0-10 之间？

            json_result = json.loads(cleaned_result)
        except Exception as e:
            raise ValueError(f"AI response is not a valid json date. Error: {e}")

        return json_result

    def _handle_retry(self, attempt: int):
        """
        处理重试逻辑，例如记录日志或等待一段时间。
        """
        wait_time = 2**attempt  # 指数退避策略：2, 4 秒
        print(f"Attempt {attempt + 1} failed. Retrying after {wait_time} seconds...")
        time.sleep(wait_time)


class TopicSummaryAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get("name")
        self.model_name = config.get("model_name")
        self.prompt = config.get("prompt")
        self.instruction = config.get("instruction")

    def do_work(self, publication, context):
        if publication.research_topics and publication.keywords:
            # 如果论文已经包含研究课题,then 直接使用
            logger.info(
                f"found existing keywords:{publication.keywords} and key research topic: {publication.research_topics}"
            )
            return {
                "keywords": publication.keywords,
                "research_topics": publication.research_topics,
            }

        if publication.keywords:
            keywords = publication.keywords
        elif publication.title:
            keywords = (
                "I dont have keywords, but I have the title: " + publication.title
            )
        else:
            keywords = (
                "I dont have keywords, and I dont have title. Please try your best."
            )
        logger.info(f"preparing prompt with keywords:{keywords}")
        prompt = self.prompt.format(
            title=publication.title,
            keywords=keywords,
            abstract=publication.abstract,
            conclusion=publication.conclusion,
        )

        logger.info(f"Prompt for Topic Summary Assistant: {prompt[:200]}")
        return self._get_response(publication=publication, prompt=prompt)


class TraigeAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get("name")
        self.model_name = config.get("model_name")
        self.prompt = config.get("prompt")
        self.instruction = config.get("instruction")

    def do_work(self, publication, context):
        """ "
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
            full_text=publication.content_raw_text[:10000],  # TODO测试阶段，限制长度
            sota_context=sota_context,
        )
        logger.info(f"Prompt for Triage Assistant: {prompt[:200]}")
        return self._get_response(publication=publication, prompt=prompt)


class DomainExpertReviewAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get("name")
        self.model_name = config.get("model_name")
        self.prompt = config.get("prompt")
        self.instruction = config.get("instruction")

    def do_work(self, publication, traige_summary, previous_review_json) -> dict:
        # update the instruction, TODO： 感觉应该有更好的地方来处理这个逻辑
        if self.name == AIAssistantType.REVIEWER_GENERAL:
            self.instruction = self.instruction.format(
                domain=publication.research_topics
            )
        else:
            # 如果是domain的专家，请专家自己来加载他的专业领域知识, TODO: 待补充考虑，现在直接pass
            pass
        # build the prompt
        if not traige_summary:
            traige_summary = "I dont have enough context, please try your best."
        if not previous_review_json:
            previous_review_json = "So far, you are the first expert to review and score this paper. please try your best to give a review and put an score to each domain."

        prompt = self.prompt.format(
            title=publication.title,
            keywords=publication.research_topics,
            abstract=publication.abstract,
            conclusion=publication.conclusion,
            traige_summary=traige_summary,
            previous_review_json=previous_review_json,
        )

        logger.info(
            f"Prompt for Domain Expert [{self.name}] Review Assistant: {prompt[:200]}"
        )
        return self._get_response(publication=publication, prompt=prompt)


class DailyReportAssistant(BaseAssistant):
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = config.get("name")
        self.model_name = config.get("model_name")
        self.prompt = config.get("prompt")
        self.instruction = config.get("instruction")

    def do_work(self, day_date: date, top_k: int, context: str):
        if not day_date:
            day_date = datetime.now().date()
        # 以下是{date}的Top {top_k} 论文的总结信息，数据为Json格式：
        #            {paper_data}
        prompt = self.prompt.format(
            date=str(day_date), top_k=top_k, paper_data=str(context)
        )

        logger.info(f"Prompt for Topic Summary Assistant: {prompt[:200]}")
        return self._get_response(publication=None, prompt=prompt)


class AIAssistantType(Enum):
    PAPER_TRIAGE = "paper_triage"
    TOPIC_SUMMARY = "topic_summary"
    REVIEWER_GENERAL = "reviewer_general"
    DOMAIN_REVIEWER_ALGORITHM = "domain_reviewer_algorithm"
    DOMAIN_REVIEWER_ARCHITECT = "domain_reviewer_architect"
    DOMAIN_REVIEWER_CLUSTER = "domain_reviewer_cluster"
    DOMAIN_REVIEWER_CHIP = "domain_reviewer_chip"
    DOMAIN_REVIEWER_NETWORK = "domain_reviewer_network"
    DAILY_REPORT_SUMMARY = "daily_report_summary"
    # xxx_domain 可以注入更多定制化的专家


class PaperReviewConfig:
    SECTION_TITLES = {
        "abstract": {"abstract"},
        "introduction": {"introduction", "background", "preliminaries", "preliminary"},
        "related_work": {
            "related work",
            "prior work",
            "literature review",
            "related studies",
        },
        "methodology": {
            "methodology",
            "methods",
            "method",
            "approach",
            "proposed method",
            "model",
            "architecture",
            "framework",
            "algorithm",
            "system design",
        },
        "experiment": {
            "experiment",
            "experiments",
            "experimental setup",
            "experiment setup",
            "setup",
            "implementation details",
            "evaluation",
            "evaluation setup",
        },
        "ablation": {"ablation", "ablation study"},
        "results": {
            "results",
            "performance",
            "findings",
            "observations",
            "empirical results",
        },
        "summary": {"summary"},
        "conclusion": {"conclusion", "final remarks", "closing remarks", "discussion"},
        "limitations": {"limitations"},
        "acknowledgments": {
            "acknowledgments",
            "acknowledgements",
            "funding",
            "author contributions",
        },
        "references": {"references", "bibliography", "cited works"},
        "appendix": {
            "appendix",
            "supplementary material",
            "supplementary",
            "additional materials",
        },
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
            "instruction": """You are a professional academic paper analysis expert with extensive experience in evaluating research papers. Your task is to read and analyze the provided core information of a research paper—including its title, keywords (if available), abstract, and conclusion. Based on this information, please extract the following:
                            1. **Core Keywords:** Summarize the key technical terms that encapsulate the main themes of the paper.
                            2. **Research Topics:** Identify the top 3 specific research topics or directions that the paper addresses. These topics should be more detailed and specific than the keywords. For example, if a keyword is "cache," a more specific research topic might be "compression methods for key-value caches."
                            Return your answer strictly in JSON format, with no extra text or annotations.""",
            "prompt": """Please evaluate the following research paper information and extract the required details:
                    Paper Information:
                    Title: {title}
                    Keywords: {keywords}
                    Abstract: {abstract}
                    Conclusion: {conclusion}
                    Based on the above information, please extract:
                    1. Core Keywords (i.e., the key technical terms that summarize the paper's main themes).
                    2. The Top 3 specific research topics or directions that the paper addresses.

                    Requirements:
                    - Use technical terminology without translating into another language.
                    - Keep the content concise.
                    - Return your answer strictly in the following JSON format, ensuring it is syntactically correct and contains no additional text or annotations:
                    {{
                        "keywords": ["keyword1", "keyword2", "keyword3", ...],
                        "research_topics": ["research_topic1", "research_topic2", "research_topic3"]
                    }}""",
        },
        AIAssistantType.PAPER_TRIAGE: {
            "name": "paper_triage",
            "model_name": "gpt-4o-mini",
            "instruction": """You are a seasoned academic paper reviewer, well-versed in the cutting-edge research trends in both academia and industry. I will provide you with the core information of a research paper—including its title, keywords, abstract, conclusion, and author details.

                    Based on this information, please analyze and answer the following six questions systematically:
                    For each of the following questions, your answer must be extremely detailed—approximately 300 words or more for each question if necessary—to ensure that your response contains the most critical and valuable information:
                    1. What is the core problem that the paper aims to solve?
                    2. What are the main technical contributions of the paper?
                    3. What innovative aspects or proposals does the paper present that are noteworthy?
                    4. Does the paper compare its approach with current state-of-the-art (SOTA) research in the field? If yes, what conclusions does it draw from this comparison?
                    5. Who are the authors of the paper, and what are their affiliated institutions? Please list them as completely as possible.
                    6. How would you assess the influence of the authors and their institutions in academia or industry? Consider whether they are associated with renowned universities, laboratories, or industrial research centers, and whether their work is widely cited or applied.

                    Please ensure your answers are accurate, professional, and strictly based on the provided paper content and background context.
                    After answering the questions, return your final evaluation in strict JSON format without any extra text or markdown formatting. The JSON must follow the exact structure shown below:
                    {{
                    "core_problem": "Provide a detailed explanation of the core problem addressed by the paper.",
                    "technical_contributions": "Provide a detailed explanation of the paper's main technical contributions.",
                    "innovations_and_proposals": [
                        "List and detail the first innovative aspect or proposal.",
                        "List and detail the second innovative aspect or proposal."
                    ],
                    "sota_comparison": "Describe whether and how the paper compares its approach with current SOTA research and state the comparison conclusions.",
                    "authors_and_affiliations": {{
                        "authors": ["Author1", "Author2"],
                        "institutions": ["Institution1", "Institution2"]
                    }},
                    "influence_assessment": "Provide a detailed assessment of the academic or industrial influence of the authors and their institutions."
                    }}""",
            "prompt": """Please evaluate the following research paper based on the instruction above. Use the paper’s core information to answer each of the six questions in detail, ensuring that your response is comprehensive and precise.

                        Paper Information:
                        Title: {title}
                        Keywords: {keywords}
                        Abstract: {abstract}
                        Conclusion: {conclusion}
                        Full Text: {full_text}
                        
                        For additional context, here are some state-of-the-art (SOTA) research outcomes in this field:
                        {sota_context}

                        Requirements:
                        - Return your response strictly in the JSON format as specified in the instruction.
                        - Do not include any extra text or markdown formatting.
                        - Ensure that the JSON is syntactically correct and can be parsed by a machine.
                        """,
        },
        AIAssistantType.REVIEWER_GENERAL: {
            "name": "reviewer_general",
            "model_name": "gpt-4o-mini",
            "instruction": """You are a seasoned expert in {domain}. You will receive the core information of a research paper, including the title, keywords (if available), abstract, and conclusion. Based on this information and the provided background context, you are required to evaluate the paper on the following five dimensions. All scores should be on a scale from 1.0 to 10.0 (scores may include up to two decimal places), where 10.0 represents the best performance. Please strictly adhere to the provided paper content and context to ensure a fair and unbiased evaluation.
                        For each of the five dimensions, please provide a detailed answer of approximately 300 words or more, explaining your reasoning thoroughly.
                        1. **Technical Innovation:** Evaluate the novelty of the method compared to existing solutions. For instance, determine whether the paper introduces a completely new mechanism or replaces traditional components with an entirely new architecture. If the work opens up a new direction or shifts community focus to a new research paradigm, a high score (above 8.0) is warranted.
                        2. **Performance Improvement:** Examine the experimental results on recognized benchmark datasets and compare them with the best previously published results. A significant improvement in key metrics should result in a high score. Consider whether the improvements are consistent across multiple tasks or datasets, demonstrating both general applicability and strong performance gains.
                        3. **Theoretical/Engineering Simplicity & Efficiency:** Assess whether the method reduces computational complexity or engineering difficulty. For example, determine if the algorithm decreases time complexity, reduces model parameters or memory usage, or shortens training/inference time. High scores are justified if the work simplifies the model architecture while maintaining or improving performance.
                        4. **Reusability & Impact:** Consider the general applicability and influence of the work. If the paper provides a model structure or algorithm that is easily transferable to other tasks and is widely adopted, it should receive a high score. Conversely, if the method is overly specialized or complex, leading to limited adoption, a lower score is appropriate.
                        5. **Author & Institutional Authority:** Review the backgrounds of the authors and their institutions. If the authors are affiliated with top-tier research institutions or have a history of influential work, and if the institution has a strong research tradition, this dimension should receive a higher score.
                        After evaluating these dimensions, please provide a recommendation on whether the paper should be read ("yes" or "no") along with your reasoning. If the paper primarily aggregates existing information without adding significant new value, you may assign low scores and explicitly state that it is not recommended.
                        Finally, please assign a confidence level to your overall evaluation on a scale from 0.0 (completely uncertain) to 1.0 (very certain), based on your analysis.
                        Return your final result in the following JSON format. Do not include any extra information or annotations, and ensure the JSON is strictly valid and provided in plain text (without any Markdown formatting):
                        {{
                            "dimensions": {{
                                "innovation": {{""score": 7.5, "reason": "Detailed explanation of the paper's technical innovation (approximately 150 words or more)."}},
                                "performance":{{""score": 5.5, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "simplicity": {{""score": 6.1, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "reusability":{{""score": 5.5, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "authority":{{""score": 8.0,"Detailed explanation of the paper's reusability and impact (approximately 150 words or more)."}}
                                }},
                            "recommend": "yes",
                            "reason": "A detailed explanation of why the paper is recommended or not, with sufficient detail."
                            "who_should_read": "Target audience description. "
                            "confidence": 0.85
                        }}""",
            "prompt": """Please evaluate the following research paper based on the instruction provided above. Provide detailed responses for each of the evaluation dimensions, with each explanation being around 300 words or more, so that the answer is thoroughly justified.：
                        Paper Information:
                        Title: {title}
                        Keywords: {keywords}
                        Abstract: {abstract}
                        Conclusion: {conclusion}
                        Additional Summary/QA: {traige_summary}
                        Based on the above information, perform your evaluation according to the instruction, and return your answer strictly in the JSON format shown in the instruction. Do not include any additional text or Markdown formatting.""",
        },
        AIAssistantType.DOMAIN_REVIEWER_ALGORITHM: {
            "name": "domain_reviewer_algorithm",
            "model_name": "gpt-4o-mini",
            "instruction": """You are a seasoned expert in the field of Computer Software and Algorithm Research, with extensive experience in reviewing academic papers. You have received the core information of a research paper along with preliminary scores provided by a general AI Reviewer for your reference.

                        Please follow these steps:

                        1. **Relevance Check:**  
                        - First, determine whether the paper is closely related to your domain (Computer Software and Algorithm Research).  
                        - If the paper is not relevant, do not modify the existing scores. Instead, return the original scores and add a confidence value (e.g., 0.4) indicating that the paper is not within your field.

                        2. **Score Review and Adjustment:**  
                        - If the paper is within your domain, carefully review the preliminary scores provided by the general reviewer.  
                        - Based on your professional judgment, perform a verification or slight adjustment of the scores.  
                        - Avoid making major changes unless you have strong professional justification. If you do modify any score, briefly explain the reason.  
                        - The evaluation dimensions include:  
                            - Innovation  
                            - Performance Improvement  
                            - Simplicity & Efficiency  
                            - Reusability & Impact  
                            - Authority (Authors and Institutions)
                        - For each of the five dimensions, please provide a detailed answer of approximately 300 words or more, explaining your reasoning thoroughly.

                        3. **Recommendation and Confidence:**  
                        - Confirm or update the recommendation (recommend) and the target readership (who_should_read).  
                        - Finally, provide a confidence level (ranging from 0.0 to 1.0, where 1.0 indicates very high confidence) in your overall evaluation.

                        ⚠️ **Important:**  
                        - Return your final result strictly in JSON format as specified below. Do not include any additional text or commentary beyond the JSON output.
                        - Ensure that the JSON is syntactically correct and machine-parsable.

                        The expected JSON format is as follows:
                        {{
                            "dimensions": {{
                                "innovation": {{""score": 7.5, "reason": "Detailed explanation of the paper's technical innovation (approximately 150 words or more)."}},
                                "performance":{{""score": 5.5, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "simplicity": {{""score": 6.1, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "reusability":{{""score": 5.5, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "authority":{{""score": 8.0,"Detailed explanation of the paper's reusability and impact (approximately 150 words or more)."}}
                                }},
                            "recommend": "yes",
                            "reason": "A detailed explanation of why the paper is recommended or not, with sufficient detail."
                            "who_should_read": "Target audience description. "
                            "confidence": 0.85
                        }}""",
            "prompt": """Please evaluate the following research paper based on the instruction provided above. You have been given the paper's core information along with the preliminary scores from the general AI Reviewer.

                        Paper Information:
                        Title: {title}
                        Keywords: {keywords}
                        Abstract: {abstract}
                        Conclusion: {conclusion}
                        Additional Summary/QA: {traige_summary}

                        Preliminary Scores (for reference):
                        {previous_review_json}
                        
                        Instructions:
                        - First, determine if the paper is relevant to your domain (Computer Software and Algorithm Research).  
                        - If it is not relevant, simply return the preliminary scores, appending a confidence value (for example, 0.4) to indicate that the paper is outside your domain.
                        - If the paper is relevant, carefully review the preliminary scores and adjust them slightly only if necessary. Avoid large changes unless absolutely required, and provide brief reasons for any modifications.
                        - Also, confirm or update the recommendation and the intended readership.
                        - Finally, assign an overall confidence level (from 0.0 to 1.0) to your evaluation.

                        Return your response strictly in the following JSON format (do not include any additional text or Markdown formatting)""",
        },
        AIAssistantType.DOMAIN_REVIEWER_ARCHITECT: {
            "name": "domain_reviewer_architect",
            "model_name": "gpt-4o-mini",
            "instruction": """You are a seasoned expert in the field of Computer Architecture, with extensive experience in reviewing academic papers and assessing state-of-the-art research in hardware design, microarchitecture, and system performance. You have received the core information of a research paper along with preliminary scores provided by a general AI Reviewer for your reference.

                        Please follow these steps:

                        1. **Relevance Check:**  
                        - First, determine whether the paper is closely related to your domain (Computer Architecture).  
                        - If the paper is not relevant, do not modify the existing scores. Instead, return the original scores and append a confidence value (e.g., 0.4) indicating that the paper is outside your field.

                        2. **Score Review and Adjustment:**  
                        - If the paper is relevant, carefully review the preliminary scores provided by the general reviewer.  
                        - Based on your professional judgment in the context of computer architecture, verify or slightly adjust the scores.  
                        - Avoid making major changes unless you have strong professional justification. If you modify any score, provide a brief explanation of your reasoning.  
                        - The evaluation dimensions include:  
                            - **Innovation:** Evaluate the novelty of the architectural design or hardware innovation (e.g., new microarchitecture, novel hardware acceleration, energy efficiency improvements).  
                            - **Performance Improvement:** Assess the improvements in performance metrics such as throughput, latency, or power efficiency compared to existing solutions.  
                            - **Simplicity & Efficiency:** Consider whether the proposed architecture simplifies design complexity, reduces resource usage, or improves system efficiency.  
                            - **Reusability & Impact:** Evaluate how adaptable the architecture is to different workloads or systems and its potential impact on the research community and industry.  
                            - **Authority (Authors and Institutions):** Consider the reputation and track record of the authors and their institutions.

                        - For each of the five dimensions, please provide a detailed explanation (approximately 300 words or more if necessary) to thoroughly justify your reasoning.

                        3. **Recommendation and Confidence:**  
                        - Confirm or update the recommendation (recommend) and the intended readership (who_should_read).  
                        - Finally, assign an overall confidence level (ranging from 0.0 to 1.0, where 1.0 indicates very high confidence) in your evaluation.

                        ⚠️ **Important:**  
                        - Return your final result strictly in JSON format as specified below. Do not include any additional text or commentary beyond the JSON output.  
                        - Ensure that the JSON is syntactically correct and machine-parsable.

                        The expected JSON format is as follows:
                        {{
                            "dimensions": {{
                                "innovation": {{""score": 7.5, "reason": "Detailed explanation of the paper's technical innovation (approximately 150 words or more)."}},
                                "performance":{{""score": 5.5, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "simplicity": {{""score": 6.1, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "reusability":{{""score": 5.5, "reason": "Detailed explanation of the paper's performance improvement (approximately 150 words or more)."}},
                                "authority":{{""score": 8.0,"Detailed explanation of the paper's reusability and impact (approximately 150 words or more)."}}
                                }},
                            "recommend": "yes",
                            "reason": "A detailed explanation of why the paper is recommended or not, with sufficient detail."
                            "who_should_read": "Target audience description. "
                            "confidence": 0.85
                        }}""",
            "prompt": """Please evaluate the following research paper based on the instruction provided above. You have been given the paper's core information along with the preliminary scores from the general AI Reviewer.

                        Paper Information:
                        Title: {title}
                        Keywords: {keywords}
                        Abstract: {abstract}
                        Conclusion: {conclusion}
                        Additional Summary/QA: {traige_summary}

                        Preliminary Scores (for reference):
                        {previous_review_json}
                        
                        Instructions:
                        - First, determine if the paper is relevant to your domain (Computer Software and Algorithm Research).  
                        - If it is not relevant, simply return the preliminary scores, appending a confidence value (for example, 0.4) to indicate that the paper is outside your domain.
                        - If the paper is relevant, carefully review the preliminary scores and adjust them slightly only if necessary. Avoid large changes unless absolutely required, and provide brief reasons for any modifications.
                        - Also, confirm or update the recommendation and the intended readership.
                        - Finally, assign an overall confidence level (from 0.0 to 1.0) to your evaluation.

                        Return your response strictly in the following JSON format (do not include any additional text or Markdown formatting)""",
        },
        # TODO: 其他领域的评审助手配置
        AIAssistantType.DAILY_REPORT_SUMMARY: {
            "name": "daily_report_summary",
            "model_name": "gpt-4o",
            "instruction": """Your task is to generate a concise, easy-to-read daily report summarizing the key insights from the top N research papers of the day. The final report should be written in Markdown format and presented as a JSON object, enabling readers to quickly understand the takeaways and feel compelled to explore more.
                    Steps:
                        1.	Global Analysis:
                        •	Theme Extraction: Analyze the provided JSON data to identify the dominant themes. Extract 3–5 primary topics from the abstracts and triage QA fields.
                        •	Innovation Clustering: Review the “innovation_reason” field to highlight clusters of technological innovations and emerging methods.
                        2.	Highlight Extraction:
                        •	Breakthrough Methods: Identify papers with an innovation_score of 8 or higher that introduce breakthrough methods.
                        •	Authoritative Research: Flag papers with an authority_score of 9 or above, especially those with renowned authors.
                        •	Reusability Potential: Highlight papers with a reusability_score of 8 or above, indicating strong potential for reuse.
                        3.	Quality and Feasibility Comparison:
                        •	Performance Comparison: Compare the dataset quality by examining SOTA comparisons in the performance_reason field.
                        •	Engineering Feasibility: Analyze the distribution of simplicity_score to assess how practical and implementable the methods are.
                        •	Anomaly Detection: Flag any papers with a confidence_score below 0.8 as potential anomalies that may require further scrutiny.
                        4.	Report Composition:
                        •	Structure & Style: Compose a concise Markdown report that includes:
                        •	A brief summary table with key metrics.
                        •	Hyperlinks to the highlighted papers.
                        •	A clear conclusion with key takeaways, using emojis (💥, 🚀, 🔥) to emphasize important points.
                        •	Tone: Combine academic rigor with an engaging, modern style. Keep the language crisp and direct—this is an introductory briefing meant to quickly inform and attract further reading, not a detailed technical analysis.

                    Output Format:

                    Return your result strictly as a JSON object with the following structure:
                    {{
                        "day_date": "YYYY-MM-DD",
                        "markdown_report": "Your concise daily report in markdown format"
                    }}""",
            "prompt": """
                    Below is the preliminary JSON summary of the top {top_k} papers for {date}:
                    {paper_data}
                    
                    In addition to the information above, please ensure your report is informative and precise—avoid vague or generic statements. You should consider the following points in your report:
                        1.	Recommendation Rationale (in less than 144 words): Include key innovation highlights, practical value, and authoritative endorsements.
                        2.	Provocative Questions (5 in total): Formulate one question each about methodology, application scenarios, and the overall impact on the field.
                        3.	Curiosity Hook: Use a “What if…?” style sentence to spark interest.

                    Your final output should be a concise Markdown report, returned as JSON in the following structure:
                    {{
                        "day_date": "YYYY-MM-DD",
                        "markdown_report": "Your concise daily report in markdown format"
                    }}
                    """,
        },
    }


class ReviewArxivPaper:
    """
    1. 初始化 OpenAI 客户端，会多次发送请求
    2. 对单一论文，首先检查论文 PDF 是否被下载，如果没有，就开启下载
    3. 对于下载好的论文，开始解析 PDF，转为文本，针对文本片段开始调用 OpenAI 的接口做分析
    4. 定义 5 个不同的 AI 助手，基于文本，对论文开始打分
    """

    def __init__(self):
        """
        初始化 OpenAI 客户端
        """
        self.client = OpenAI()

    def _get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def process(self, paper: "ArxivPaper") -> PaperScores:
        """
        处理单篇论文
        """
        logger.info(f"Processing paper: “{paper.title}”")
        db = None
        try:

            # 检查 PDF 是否已经下载
            full_path, relative_path = self._get_pdf_path(paper)
            if not self._is_pdf_downloaded(paper):
                logger.info(f"PDF not downloaded, downloading now: {paper.pdf_url}")
                full_path, relative_path = self._download_pdf(paper)

            if not full_path or not relative_path:
                logger.error(f"Failed to locate the PDF for paper: {paper.title}")
                return None
            logger.info(f"Found the paper PDF file in: {relative_path}")

            # 检查 Publication 是否已经存在
            db = next(self._get_db())
            publication = (
                db.query(Publication)
                .filter(Publication.paper_id == paper.arxiv_id)
                .first()
            )
            if not publication:
                logger.info(
                    f"Publication not found in database, creating new entry for: {paper.title}"
                )
                # 1. 简单处理，去掉空行
                text = self._parse_pdf_to_text(full_path)
                text_lines = [line.strip() for line in text.split("\n") if line.strip()]
                # 2. 论文的一些典型识别标题
                title_indices = self._detect_section_titles(text_lines)
                # 3. 按标题拆分
                section_chunks = self._split_to_chunks_by_title(
                    text_lines, title_indices
                )
                # 4. 选出重点内容
                abstract_text = "\n".join(
                    section_chunks.get("abstract", "")
                )  # convert to string
                conclusion_text = "\n".join(section_chunks.get("conclusion", ""))
                references_text = "\n".join(section_chunks.get("references", ""))
                if title_indices.get("refernces"):
                    # main context 取到 references 之前的所有内容
                    main_context = "\n".join(
                        text_lines[0 : section_chunks.get("references")]
                    )
                else:
                    # 如果没有 references，简单取全文
                    main_context = text
                logger.info(f"abstract_text: {abstract_text[:100]}")
                logger.info(f"conclusion_text: {conclusion_text[:100]}")
                logger.info(f"Main context extracted from PDF: {main_context[:200]}...")
                # 新建一个publication
                publication = Publication(
                    paper_id=paper.arxiv_id,
                    instance_id=0,  # 默认关联到一个非会议
                    title=self._clean_db_str_input(paper.title),
                    year=paper.published.strftime("%Y"),
                    publish_date=paper.published,
                    tldr="",
                    abstract=self._clean_db_str_input(
                        paper.summary if paper.summary else abstract_text
                    )[
                        :5000
                    ],  # TODO: 有没有更好的办法处理，当前默认conclusion/abstract在5000字符以内
                    conclusion=self._clean_db_str_input(conclusion_text)[
                        :5000
                    ],  # TODO: 有没有更好的办法处理，当前默认conclusion/abstract在5000字符以内
                    content_raw_text=self._clean_db_str_input(main_context),
                    reference_raw_text=self._clean_db_str_input(references_text),
                    pdf_path=relative_path,  # 存储相对路径，方便系统迁移
                    citation_count=0,
                    award="",
                    doi="",
                    url="",
                    pdf_url=paper.pdf_url,
                    attachment_url="",
                )
                # 先保存到数据库
                db.add(publication)
                logger.info(f"Saving publication to database: {publication.title}")
                db.commit()
                db.refresh(publication)

            # 然后交给评审打分
            scores = self._review_paper_with_ai_experts(publication)
            db.add(publication)
            db.add(scores)
            db.commit()

            db.refresh(scores)
            return scores

        except SQLAlchemyError as db_err:
            db.rollback()
            logger.error(
                f"Database error occurred while processing paper “{paper.title}”: {db_err}"
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing paper “{paper.title}”: {e}"
            )
        finally:
            if db:
                db.close()

        return None

    def process_batch(self, paper_list: List["ArxivPaper"]) -> List[PaperScores]:
        """
        批量处理论文
        """
        # TODO: 一次处理50篇论文，试运行稳定后删除
        paper_list = paper_list[:50]
        results = []
        # 使用线程池并发处理
        max_threads = 4  # 根据您的系统和任务需求调整线程数
        with ThreadPoolExecutor(max_threads) as executor:
            # 提交所有任务
            future_to_paper = {
                executor.submit(self.process, paper): paper for paper in paper_list
            }
            # 等待所有任务完成
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    results.append(future.result())  # 获取线程执行结果
                except Exception as exc:
                    logger.error(f"{paper} 处理时发生异常: {exc}")

        return results

    def get_ai_daily_report(self, report_day: date, top_k: int, context: str) -> str:
        # 调用大模型来撰写每日报告 TODO: 这个函数不应该放在这个类，待改进
        # step 1: 是否数据库已经生成了，如果有，就直接返回
        # step 2: 调用大模型来做
        daily_summary_config = PaperReviewConfig.ai_assistants_config[
            AIAssistantType.DAILY_REPORT_SUMMARY
        ]
        daily_report_assistant = DailyReportAssistant(daily_summary_config)
        logger.info(
            f"calling {daily_report_assistant.name} to generate daily report for date: {report_day}"
        )
        report_result = daily_report_assistant.do_work(
            day_date=report_day, top_k=top_k, context=context
        )
        return report_result

    def _detect_section_titles(self, lines):
        """检测标题行，返回标题行索引"""
        title_indices = {}
        section_num = 0  # 对于 summary、limitation 这类标题，可能在多个位置出现，需要全部保留。加一个编码，保证独立
        for i, line in enumerate(lines):
            clean_line = re.sub(r"[^a-zA-Z\s]", "", line).strip().lower()
            for section, keywords in PaperReviewConfig.SECTION_TITLES.items():
                if any(
                    re.match(
                        rf"^\s*(\d+([\.\-）]\d+)*[\.\-）]*\s*)?{re.escape(kw)}\s*$",
                        clean_line,
                        re.IGNORECASE,
                    )
                    for kw in keywords
                ):
                    if section in title_indices:
                        title_indices[section + "_" + str(section_num)] = i
                        section_num += 1
                    else:
                        title_indices[section] = i
                    break
        return title_indices

    def _split_to_chunks_by_title(self, lines, title_indices):
        """按照标题行分块"""
        chunks = defaultdict(list)
        sorted_sections = sorted(
            title_indices.items(), key=lambda x: x[1]
        )  # 按出现顺序排序

        for idx, (section, start_idx) in enumerate(sorted_sections):
            end_idx = (
                sorted_sections[idx + 1][1]
                if idx + 1 < len(sorted_sections)
                else len(lines)
            )
            chunks[section] = lines[start_idx:end_idx]

        return chunks

    def _get_pdf_path(self, paper):
        """
        根据论文信息生成对应的 PDF 存储路径。
        假设 paper.date 是 'YYYY-MM-DD' 格式的字符串，paper.arxiv_id 是论文的唯一标识符。
        """
        try:
            # 解析日期字符串
            year = paper.published.strftime("%Y")
            month = paper.published.strftime("%m")
            # 构建相对路径
            relative_path = f"./pdf/{year}/{month}/{paper.arxiv_id}.pdf"
            # 从配置文件中获取 PDF 存储目录
            data_storage_dir = get_data_storage_dir()
            # 构建完整路径
            full_path = data_storage_dir / relative_path

            logger.info(f"search PDF relative path: {relative_path}")
            # 如果目录不存在，则创建
            full_path.parent.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Error generating PDF path: {e}")
            raise e
        # 返回 PDF 存储目录和文件路径
        return str(full_path), str(relative_path)

    def _is_pdf_downloaded(self, paper: "ArxivPaper") -> bool:
        """
        检查论文的 PDF 是否已下载
        """
        # 实现检查逻辑
        logger.info(f"Checking if PDF is downloaded for paper: {paper.title}")
        full_path, relative_path = self._get_pdf_path(paper)
        logger.info(f"Checking if PDF exists at: {relative_path}")
        return os.path.exists(full_path)

    def _download_pdf(self, paper: "ArxivPaper"):
        """
        下载论文的 PDF 并保存到指定路径。
        """
        full_path, relative_path = self._get_pdf_path(paper)
        try:
            response = requests.get(paper.pdf_url, timeout=10)  # 设置超时时间为10秒
            response.raise_for_status()  # 如果响应状态码不是 200，将引发 HTTPError 异常
            with open(full_path, "wb") as f:
                f.write(response.content)
            logging.info(f"PDF downloaded and saved to {relative_path}")
            return full_path, relative_path
        except requests.HTTPError as http_err:
            logging.error(f"HTTP error occurred while downloading PDF: {http_err}")
        except ConnectionError as conn_err:
            logging.error(
                f"Connection error occurred while downloading PDF: {conn_err}"
            )
        except Timeout as timeout_err:
            logging.error(
                f"Timeout error occurred while downloading PDF: {timeout_err}"
            )
        except requests.RequestException as req_err:
            logging.error(f"An error occurred while downloading PDF: {req_err}")
        except IOError as io_err:
            logging.error(f"File operation error: {io_err}")
        return None

    def _parse_pdf_to_text(self, pdf_path) -> str:
        """
        解析 PDF 并将其转换为文本
        """
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            # print(page.number, page.get_text()[:20])
            text += page.get_text()
        logger.info(
            f"PDF parsed to text, page count{len(doc)}, text length: {len(text)}"
        )
        return text

    def _review_paper_with_ai_experts(self, publication: Publication) -> PaperScores:
        """
        使用 OpenAI 接口分析文本，并根据不同标准进行评分
        """
        try:
            # 0. 先让论文总结研究的关键方向
            topic_summary_config = PaperReviewConfig.ai_assistants_config[
                AIAssistantType.TOPIC_SUMMARY
            ]
            topic_summary_assistant = TopicSummaryAssistant(topic_summary_config)
            logger.info(
                f"calling {topic_summary_assistant} to process paper {publication.paper_id}"
            )
            topic_result = topic_summary_assistant.do_work(publication, context="")
            logger.info(f"Topic summary result: {topic_result}")

            # 1. 让AI总结论文的几个关键问题, 以及答案，辅助推理
            if topic_result:
                publication.keywords = topic_result.get("keywords", [])
                publication.research_topics = topic_result.get("research_topics", [])

            traige_assistant_config = PaperReviewConfig.ai_assistants_config[
                AIAssistantType.PAPER_TRIAGE
            ]
            traige_assistant = TraigeAssistant(traige_assistant_config)
            context = ""
            if publication.research_topics:
                context = (
                    f"Here are some key research topics: {publication.research_topics}"
                )
            traige_summary = traige_assistant.do_work(publication, context)
            # save traige result
            if traige_summary:
                publication.triage_qa = traige_summary
            logger.info(f"Triaging result: {traige_summary}")

            # 2. 让AI 根据初步的信息来打分，自动检索相关核心问题的state of the art 研究成果作为补充判断
            reviwer_general = PaperReviewConfig.ai_assistants_config[
                AIAssistantType.REVIEWER_GENERAL
            ]
            reviewer_general_assistant = DomainExpertReviewAssistant(reviwer_general)
            init_score = reviewer_general_assistant.do_work(
                publication, traige_summary=traige_summary, previous_review_json=""
            )
            logger.info(f"Initial score is: {init_score}")

            # 2.1. 处理初步评分结果
            score = PaperScores(
                paper_id=publication.paper_id,
                title=publication.title,
                ai_reviewer=reviewer_general_assistant.name,
                review_status="pending",
                error_message="",
                log=f"AI reviewer {reviewer_general_assistant.name} reviewed the paper and provided initial score.",
            )
            score = self._assign_score_values(score=score, json_score=init_score)
            score.review_status = "completed"
            logger.info(f"sucessfully init a score object: {score}")

            # 3: 遍历领域专家，对打分进行核查和修正
            domain_reviwers = self._load_domain_review_assistants()
            for expert_name, expert_assistant in domain_reviwers.items():
                logger.info(
                    f"Processing paper“ {publication.paper_id} ” with expert {expert_name}"
                )
                expert_score = expert_assistant.do_work(
                    publication,
                    traige_summary=traige_summary,
                    previous_review_json=init_score,
                )
                if expert_score and expert_score.get("confidence"):
                    # 判断和合并专家的结果
                    if expert_score.get("confidence") > score.confidence_score:
                        logger.info(
                            f"Expert {expert_name} provided a valid review/updates."
                        )
                        score = self._assign_score_values(
                            score=score, json_score=expert_score
                        )
                        score.ai_reviewer = expert_assistant.name
                        score.review_status = "rewrited by expert"
                        score.error_message = ""
                        score.log = "\n".join(
                            [
                                score.log,
                                f"Expert {expert_name} reviewed the paper and provided update: {score.get_review_status()}",
                            ]
                        )
                    else:
                        score.log = "\n".join(
                            [
                                score.log,
                                f"Expert {expert_name} reviewed the paper, but confidence is low.",
                            ]
                        )
                else:
                    score.log = "\n".join(
                        [
                            score.log,
                            f"Expert {expert_name} reviewed the paper but no valid score provided.",
                        ]
                    )

            logger.info(
                f"Congratulate, AI experts reviewed the paper and the final status are: {score.get_review_status()}"
            )
            return score
        except Exception as e:
            logger.error(f"Error processing paper “{publication.paper_id}”: {e}")
            raise e

    def _assign_score_values(self, score: PaperScores, json_score: dict):
        if not json_score or not json_score.get("dimensions"):
            raise ValueError("Invalid json data, unable to retrieve score data.")
        dimensions = json_score.get("dimensions")
        score.innovation_score = (
            0.0
            if not dimensions.get("innovation")
            else dimensions.get("innovation").get("score", 0.0)
        )
        score.innovation_reason = (
            "N/A"
            if not dimensions.get("innovation")
            else dimensions.get("innovation").get("reason", "N/A")
        )
        score.performance_score = (
            0.0
            if not dimensions.get("performance")
            else dimensions.get("performance").get("score", 0.0)
        )
        score.performance_reason = (
            "N/A"
            if not dimensions.get("performance")
            else dimensions.get("performance").get("reason", "N/A")
        )
        score.simplicity_score = (
            0.0
            if not dimensions.get("simplicity")
            else dimensions.get("simplicity").get("score", 0.0)
        )
        score.simplicity_reason = (
            "N/A"
            if not dimensions.get("simplicity")
            else dimensions.get("simplicity").get("reason", "N/A")
        )
        score.reusability_score = (
            0.0
            if not dimensions.get("reusability")
            else dimensions.get("reusability").get("score", 0.0)
        )
        score.reusability_reason = (
            "N/A"
            if not dimensions.get("reusability")
            else dimensions.get("reusability").get("reason", "N/A")
        )
        score.authority_score = (
            0.0
            if not dimensions.get("authority")
            else dimensions.get("authority").get("score", 0.0)
        )
        score.authority_reason = (
            "N/A"
            if not dimensions.get("authority")
            else dimensions.get("authority").get("reason", "N/A")
        )

        # Calculate the weighted score and round it to 2 decimal places
        score.weighted_score = round(
            0.35 * score.innovation_score
            + 0.25 * score.performance_score
            + 0.15 * score.simplicity_score
            + 0.15 * score.reusability_score
            + 0.1 * score.authority_score,
            2,
        )
        # Assign other fields directly from the JSON
        score.recommend = str(json_score.get("recommend", False)).lower() in (
            "yes",
            "true",
            "1",
        )
        score.recommend_reason = json_score.get("reason", "")
        score.who_should_read = json_score.get("who_should_read", "")
        score.confidence_score = json_score.get("confidence", 0.0)

        return score

    def _load_domain_review_assistants(
        self,
    ) -> Dict[AIAssistantType, DomainExpertReviewAssistant]:
        assistants = {}
        # 只加载domain_xxx的专家。 TODO： 这里的逻辑可以再优化，当前简单按字符串过滤
        for assistant_type, config in PaperReviewConfig.ai_assistants_config.items():
            if not assistant_type.value.lower().startswith("domain_reviewer"):
                continue
            assistants[assistant_type] = DomainExpertReviewAssistant(config)
            logger.info(f"Loaded domain review assistants: {assistant_type}'")
        return assistants

    def _clean_db_str_input(self, text: str):
        if text is None:
            return ""
        # Remove NUL characters
        text = text.replace("\x00", "")
        return text
