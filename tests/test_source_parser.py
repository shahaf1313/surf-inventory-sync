import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.source_parser import (  # noqa: E402
    filter_new_items,
    parse_manufacturer_file,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_manufacturer_orderform.xlsx"


def test_parses_consolidated_sheet_only():
    rows = parse_manufacturer_file(FIXTURE, sheet_names=["North ALL products "])
    assert len(rows) == 660


def test_filters_new_and_new_size_items_case_insensitively():
    rows = parse_manufacturer_file(FIXTURE, sheet_names=["North ALL products "])
    new_rows = filter_new_items(rows)
    # 154 'New' + 17 'New sizes' + 1 'NEW' observed in the sample file.
    assert len(new_rows) == 172
    statuses = {r.status.strip().lower() for r in new_rows}
    assert statuses <= {"new", "new sizes"}


def test_carry_over_rows_are_excluded():
    rows = parse_manufacturer_file(FIXTURE, sheet_names=["North ALL products "])
    new_rows = filter_new_items(rows)
    assert all("carry" not in (r.status or "").lower() for r in new_rows)


def test_sku_is_stable_and_unique_per_size():
    rows = parse_manufacturer_file(FIXTURE, sheet_names=["North ALL products "])
    skus = [r.sku for r in rows]
    assert len(skus) == len(set(skus)), "expected one unique SKU per item+color+size row"


def test_reading_all_sheets_without_explicit_names_does_not_crash():
    rows = parse_manufacturer_file(FIXTURE)
    assert len(rows) > 0
