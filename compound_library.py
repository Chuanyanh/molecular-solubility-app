import csv
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data_library"

@lru_cache(maxsize=1)
def load_compounds():
    compounds = json.loads(
        (ROOT / "compounds.json").read_text(encoding="utf-8")
    )
    with (ROOT / "aqsoldb_search_catalog.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            compounds.append({
                "id": "aqsoldb:" + row["ID"],
                "name_zh": "",
                "name_en": row["Name"],
                "aliases": [row["ID"]],
                "smiles": row["canonical_smiles"],
                "formula": "",
                "source": "AqSolDB",
            })
    return compounds

def search_compounds(query):
    query = query.strip().casefold()
    compounds = load_compounds()
    if not query:
        return compounds[:40]

    matches = [
        item for item in compounds
        if any(
            query in text.casefold()
            for text in [
                item["name_zh"], item["name_en"], item.get("formula", ""), *item["aliases"]
            ]
        )
    ]
    return sorted(
        matches,
        key=lambda item: (
            not any(
                query == text.casefold()
                for text in [
                    item["name_zh"], item["name_en"], item.get("formula", ""), *item["aliases"]
                ]
            ),
            item["name_en"].casefold(),
            item["id"]
        )
    )
