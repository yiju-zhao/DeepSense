"""
python_arXiv_parsing_example.py

This sample script illustrates a basic arXiv api call
followed by parsing of the results using the 
feedparser python module.

Please see the documentation at 
http://export.arxiv.org/api_help/docs/user-manual.html
for more information, or email the arXiv api 
mailing list at arxiv-api@googlegroups.com.

urllib is included in the standard python library.
feedparser can be downloaded from http://feedparser.org/ .

Author: Julius B. Lucks

This is free software.  Feel free to do what you want
with it, but please play nice with the arXiv API!
"""

import random
import sys
import time
import logging
import os
from typing import Any, Dict, List, Optional
import feedparser
import requests
from .base_crawler import ApiArgs, BaseCrawler
import xml.etree.ElementTree as ET

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

class ArxivApiArgs(ApiArgs):
    search_query: str
    start: int
    max_results: int
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = None

class ArxivCrawler(BaseCrawler):
    def get_api_response(self, url: str, args: ArxivApiArgs) -> Dict[str, Any]:
        # perform a GET request using the base_url and query
        # query = f'search_query=au:{affiliation_name}&start={start}&max_results={max_results}&sortBy=lastUpdatedDate&sortOrder=ascending'
        # 检查 sortBy 是否为空或未提供
        # 检查 sortBy 是否为空或未提供
        if args.sortBy is None or args.sortBy == "":
            sort_by = "submittedDate"  # 可以设置默认值
        else:
            sort_by = args.sortBy

        # 检查 sortOrder 是否为空或未提供
        if args.sortOrder is None or args.sortOrder == "":
            sort_order = "descending"  # 可以设置默认值
        else:
            sort_order = args.sortOrder
        query = f'search_query={args.search_query}&start={args.start}&max_results={args.max_results}&sortBy={sort_by}&sortOrder={sort_order}'
        logger.info(f'featch the api response from:{url}{query}')
        # perform a GET request using the base_url and query
        response = requests.get(url + query)
        xml_data = response.text  # 这是原始的 XML 字符串
        # dummy_data = get_arxiv_dummy_data()
        # 解析 XML 数据, 为什么不用 feedparser 解析呢？-- 它不能很好地处理affiliation, 因此定制一个解析函数parse_arxiv_feed
        #TODO 还要考虑分页的情况，当前可以简单地将 max_results 设置为 1000
        result = self.parse_arxiv_feed(xml_data)
        return result
    
    @staticmethod
    def parse_arxiv_feed(xml_data: str) -> dict:
        """
        解析 arXiv API 返回的 XML 数据，提取 feed 信息和论文条目，并返回为字典格式。
        参数:
            xml_data: str - 包含 arXiv API 响应的 XML 数据字符串。
        返回:
            dict: 包含 feed 信息和论文条目的字典.
        """
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "arxiv": "http://arxiv.org/schemas/atom"
        }
        root = ET.fromstring(xml_data)

        feed_info = {
            "feed_title": root.find("atom:title", ns).text,
            "updated": root.find("atom:updated", ns).text,
            "total_results": root.find("opensearch:totalResults", ns).text,
            "items_per_page": root.find("opensearch:itemsPerPage", ns).text,
            "start_index": root.find("opensearch:startIndex", ns).text
        }

        papers = []
        for entry in root.findall("atom:entry", ns):
            # 提取 primary_category
            primary_category_elem = entry.find("arxiv:primary_category", ns)
            primary_category = primary_category_elem.attrib.get("term") if primary_category_elem is not None else None

            # 提取所有 category（默认命名空间下）
            categories = []
            for cat in entry.findall("atom:category", ns):
                term = cat.attrib.get("term")
                if term:
                    categories.append(term)
            # find PDF url: <link title="pdf" href="http://arxiv.org/pdf/1504.01441v3" rel="related" type="application/pdf"/>
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if (link.attrib.get("type") == "application/pdf" and 
                    link.attrib.get("title") == "pdf"):
                    pdf_url = link.attrib["href"]
                    break  # 找到就跳出循环
        
            paper = {
                "arxiv_id": entry.find("atom:id", ns).text.rsplit('/', 1)[-1], # 只保留数字ID部分：比如1504.01441v3
                "title": entry.find("atom:title", ns).text,
                "pdf_url": pdf_url,
                "published": entry.find("atom:published", ns).text,
                "summary": entry.find("atom:summary", ns).text.strip() if entry.find("atom:summary", ns) is not None else "",
                "authors": [],
                "primary_category": primary_category,
                "categories": categories
            }
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text
                aff_list = [aff.text for aff in author.findall("arxiv:affiliation", ns)]
                paper["authors"].append({"name": name, "affiliations": aff_list})
            papers.append(paper)

        return {
            "feed_info": feed_info,
            "papers": papers
        }

def get_arxiv_dummy_data():
    try:
        delay = random.randint(1, 10)  # 随机延迟 1 到 10 秒
        time.sleep(delay)  # 模拟网络延迟
        # Get the path to the local file
        file_path = os.path.join(os.path.dirname(__file__), "arxiv_dummy_data.xml")
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Could not find arxiv_dummy_data.xml at {file_path}")
        # Read and validate file content
        with open(file_path, "r", encoding="utf-8") as file:
            response = file.read()
            
        if not response:
            logger.error("File is empty")
            raise ValueError("arxiv_dummy_data.xml is empty")
            
        logger.info(f"Successfully read {len(response)} bytes from file")
        return response
    
    except Exception as e:
        logger.error(f"Error simulating network delay: {e}")
    





