
import os
import csv
import sys
import calendar
from pathlib import Path
from datetime import date

import pyalex
from pyalex import Works


KEYWORD = "Bitcoin"
CSV_FILE = "bitcoin_papers.csv"
MD_FILE = "bitcoin_papers.md"
MAX_PAPERS = 500
PER_PAGE = 100

TODAY = date.today()
START_YEAR = TODAY.year - 2
START_DATE = date(
    START_YEAR,
    TODAY.month,
    min(TODAY.day, calendar.monthrange(START_YEAR, TODAY.month)[1])
)


def reconstruct_abstract(index):
    """还原 OpenAlex 提供的论文摘要。"""
    if not index:
        return ""

    words = []
    for word, positions in index.items():
        for position in positions:
            words.append((position, word))

    words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in words)


def escape_markdown(text):
    text = str(text or "")
    for char in ["\\", "`", "*", "_", "[", "]", "|"]:
        text = text.replace(char, "\\" + char)
    return text.replace("\n", " ").replace("\r", " ")


def valid_url(url):
    url = str(url or "").strip()
    if url.startswith("https://") or url.startswith("http://"):
        return url
    return ""


def get_links(paper):
    primary = paper.get("primary_location") or {}
    best = paper.get("best_oa_location") or {}

    doi = paper.get("doi") or ""
    doi_url = doi if doi.startswith("http") else (
        "https://doi.org/" + doi if doi else ""
    )

    article = (
        valid_url(best.get("landing_page_url"))
        or valid_url(primary.get("landing_page_url"))
        or valid_url(doi_url)
        or valid_url(paper.get("id"))
    )

    pdf = (
        valid_url(best.get("pdf_url"))
        or valid_url(primary.get("pdf_url"))
    )

    return article, pdf


def main():
    api_key = os.environ.get("OPENALEX_API_KEY")

    if not api_key:
        print("错误：没有读取到 OpenAlex API 密钥")
        sys.exit(1)

    pyalex.config.api_key = api_key

    print(f"搜索关键词：{KEYWORD}")
    print(f"论文起始日期：{START_DATE}")
    print(f"最多收集：{MAX_PAPERS} 篇")

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
    papers = []

    for page in pages:
        for paper in page:
            doi = (paper.get("doi") or "").strip().lower()
            paper_id = paper.get("id") or ""
            unique_id = doi if doi else paper_id

            if not unique_id or unique_id in seen:
                continue

            seen.add(unique_id)

            authors = []
            for item in (paper.get("authorships") or []):
                author = item.get("author") or {}
                name = author.get("display_name")
                if name:
                    authors.append(name)

            abstract = reconstruct_abstract(
                paper.get("abstract_inverted_index")
            )

            article_url, pdf_url = get_links(paper)

            papers.append({
                "title": paper.get("title") or "无标题",
                "authors": "; ".join(authors),
                "date": paper.get("publication_date") or "",
                "year": paper.get("publication_year") or "",
                "citations": paper.get("cited_by_count") or 0,
                "doi": paper.get("doi") or "",
                "url": article_url,
                "pdf": pdf_url,
                "abstract": abstract
            })

            if len(papers) >= MAX_PAPERS:
                break

        if len(papers) >= MAX_PAPERS:
            break

    papers.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    # 生成 CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        writer.writerow([
            "标题", "作者", "发表日期", "发表年份",
            "引用次数", "DOI", "论文链接", "摘要", "PDF链接"
        ])

        for p in papers:
            writer.writerow([
                p["title"], p["authors"], p["date"],
                p["year"], p["citations"], p["doi"],
                p["url"], p["abstract"], p["pdf"]
            ])

    # 生成 GitHub 阅读页面
    with open(MD_FILE, "w", encoding="utf-8") as file:
        file.write("# Bitcoin 论文每日追踪\n\n")
        file.write(f"- 更新时间：{TODAY}\n")
        file.write(f"- 收录范围：{START_DATE} 至 {TODAY}\n")
        file.write(f"- 论文数量：{len(papers)} 篇\n")
        file.write("- 数据来源：OpenAlex\n\n")
        file.write("点击论文标题打开原文；有公开 PDF 时可点击 PDF 链接。\n\n")
        file.write("---\n\n")

        for i, p in enumerate(papers, 1):
            title = escape_markdown(p["title"])
            authors = escape_markdown(p["authors"] or "未提供")
            abstract = escape_markdown(
                p["abstract"] or "OpenAlex 暂未提供摘要。"
            )

            file.write(f"## {i}. [{title}](<{p['url']}>)\n\n")
            file.write(f"- 作者：{authors}\n")
            file.write(f"- 发表日期：{p['date'] or '未提供'}\n")
            file.write(f"- 引用次数：{p['citations']}\n")

            if p["doi"]:
                file.write(f"- DOI：{p['doi']}\n")

            if p["pdf"]:
                file.write(f"- [打开 PDF](<{p['pdf']}>)\n")

            file.write("\n**摘要：**\n\n")
            file.write(abstract + "\n\n")
            file.write("---\n\n")

    abstract_count = sum(1 for p in papers if p["abstract"])
    pdf_count = sum(1 for p in papers if p["pdf"])

    print("=" * 40)
    print(f"搜索完成，共收集 {len(papers)} 篇论文")
    print(f"有摘要：{abstract_count} 篇")
    print(f"有 PDF 链接：{pdf_count} 篇")
    print(f"生成文件：{CSV_FILE} 和 {MD_FILE}")
    print("=" * 40)


if __name__ == "__main__":
    main()
