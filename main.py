
import csv
from pathlib import Path
from pyalex import Works

KEYWORD = "Bitcoin"
OUTPUT_FILE = "bitcoin_papers.csv"
MAX_PAPERS = 500


def main():
    print(f"正在搜索：{KEYWORD}")

    papers = Works().search(KEYWORD).paginate(
        per_page=100,
        n_max=MAX_PAPERS
    )

    count = 0

    with Path(OUTPUT_FILE).open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "标题", "作者", "发表年份",
            "引用次数", "DOI", "论文链接"
        ])

        for paper in papers:
            authors = []
            for item in paper.get("authorships", []):
                author = item.get("author") or {}
                name = author.get("display_name")
                if name:
                    authors.append(name)

            location = paper.get("primary_location") or {}

            writer.writerow([
                paper.get("title") or "",
                "; ".join(authors),
                paper.get("publication_year") or "",
                paper.get("cited_by_count") or 0,
                paper.get("doi") or "",
                location.get("landing_page_url") or paper.get("id", "")
            ])
            count += 1

    print(f"完成！共收集 {count} 篇论文。")


if __name__ == "__main__":
    main()
