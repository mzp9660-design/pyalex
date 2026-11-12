
import os
import csv
import sys
from pathlib import Path

import pyalex
from pyalex import Works


# ===== 基本设置 =====
KEYWORD = "Bitcoin"
OUTPUT_FILE = "bitcoin_papers.csv"
MAX_PAPERS = 500
PER_PAGE = 100


def main():
    # 读取 GitHub 保存的 API 密钥
    api_key = os.environ.get("OPENALEX_API_KEY")

    if not api_key:
        print("错误：没有读取到 OpenAlex API 密钥")
        sys.exit(1)

    pyalex.config.api_key = api_key

    print(f"开始搜索：{KEYWORD}")
    print(f"最多收集：{MAX_PAPERS} 篇论文")

    # 创建搜索任务
    query = Works().search(KEYWORD)

    # 分页获取论文
    pages = query.paginate(
        per_page=PER_PAGE,
        n_max=MAX_PAPERS
    )

    count = 0

    # 创建 CSV 文件
    with Path(OUTPUT_FILE).open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "标题",
            "作者",
            "发表年份",
            "引用次数",
            "DOI",
            "论文链接"
        ])

        # 每一页包含多篇论文
        for page in pages:
            for paper in page:

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
                    paper.get("publication_year") or "",
                    paper.get("cited_by_count") or 0,
                    paper.get("doi") or "",
                    landing_page or paper.get("id", "")
                ])

                count += 1

                if count >= MAX_PAPERS:
                    break

            if count >= MAX_PAPERS:
                break

    print("=" * 40)
    print(f"搜索完成！共收集 {count} 篇论文。")
    print(f"结果文件：{OUTPUT_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    main()
