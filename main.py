
import os
import csv
import sys
from pathlib import Path
from datetime import date

import pyalex
from pyalex import Works


# ===== 基本设置 =====
KEYWORD = "Bitcoin"
OUTPUT_FILE = "bitcoin_papers.csv"
MAX_PAPERS = 500
PER_PAGE = 100

# 只收集最近两年的论文
TODAY = date.today()
START_DATE = TODAY.replace(year=TODAY.year - 2)


def main():
    # 读取 GitHub Secrets 中的 API 密钥
    api_key = os.environ.get("OPENALEX_API_KEY")

    if not api_key:
        print("错误：没有读取到 OpenAlex API 密钥")
        sys.exit(1)

    pyalex.config.api_key = api_key

    print(f"搜索关键词：{KEYWORD}")
    print(f"论文起始日期：{START_DATE}")
    print(f"最多收集：{MAX_PAPERS} 篇")

    # 搜索最近两年的论文，并按发表日期倒序排列
    query = (
        Works()
        .search(KEYWORD)
        .filter(from_publication_date=START_DATE.isoformat())
        .sort(publication_date="desc")
    )

    pages = query.paginate(
        per_page=PER_PAGE,
        n_max=MAX_PAPERS
    )

    seen = set()
    count = 0

    # 每次重新生成最新论文文件
    with Path(OUTPUT_FILE).open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "标题",
            "作者",
            "发表日期",
            "发表年份",
            "引用次数",
            "DOI",
            "论文链接"
        ])

        for page in pages:
            for paper in page:

                doi = (paper.get("doi") or "").strip().lower()
                paper_id = paper.get("id") or ""

                # 优先使用 DOI 去重，没有 DOI 时使用 OpenAlex ID
                unique_id = doi if doi else paper_id

                if not unique_id or unique_id in seen:
                    continue

                seen.add(unique_id)

                authors = []

                for item in paper.get("authorships", []):
                    author = item.get("author") or {}
                    name = author.get("display_name")

                    if name:
                        authors.append(name)

                location = paper.get("primary_location") or {}
                landing_page = location.get("landing_page_url")

                writer.writerow([
                    paper.get("title") or "",
                    "; ".join(authors),
                    paper.get("publication_date") or "",
                    paper.get("publication_year") or "",
                    paper.get("cited_by_count") or 0,
                    paper.get("doi") or "",
                    landing_page or paper_id
                ])

                count += 1

                if count >= MAX_PAPERS:
                    break

            if count >= MAX_PAPERS:
                break

    print("=" * 40)
    print(f"搜索完成，共收集 {count} 篇论文")
    print(f"论文时间范围：{START_DATE} 至 {TODAY}")
    print(f"结果文件：{OUTPUT_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    main()
