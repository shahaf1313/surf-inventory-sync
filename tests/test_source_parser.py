import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.source_parser import (  # noqa: E402
    ProductRow,
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


def test_auto_sheet_selection_avoids_double_counting_the_consolidated_sheet():
    # The fixture has a "North ALL products" sheet plus per-category sheets
    # that repeat the same rows. Auto-selection (no explicit sheet_names)
    # must land on the same 660 rows as reading the consolidated sheet alone,
    # not the ~1600+ rows naively concatenating every sheet would produce.
    explicit = parse_manufacturer_file(FIXTURE, sheet_names=["North ALL products "])
    auto = parse_manufacturer_file(FIXTURE)
    assert len(auto) == len(explicit) == 660
    assert len(filter_new_items(auto)) == 172


def _make_row(status: str | None) -> ProductRow:
    """Minimal ProductRow for exercising is_new_or_new_size() directly -
    none of the real fixture files happen to contain a price-only-update
    status, so this is the only way to cover that case."""
    return ProductRow(
        ranking="1",
        sub_group="Group",
        segment="Segment",
        item_code="12345",
        barcode="000",
        description="Test Item",
        color_code="1",
        color_description="Black",
        size="M",
        status=status,
        retail_price=100,
        wholesale_price=50,
        order_qty=0,
        order_amount=0,
        source_sheet="Sheet",
    )


def test_price_only_updates_are_not_treated_as_new():
    # A price change on an existing item isn't interesting to dad - only
    # genuinely new products/sizes/colors are. No real order form has used
    # this exact status text yet, but the filter must not include it if one
    # ever does (a naive "contains 'new'" check would wrongly match it).
    for status in ("New price", "New Price", "NEW PRICE", "new price "):
        assert _make_row(status).is_new_or_new_size() is False, status


def test_genuinely_new_statuses_still_match():
    for status in ("New", "NEW", "New sizes", "New colour", "New Colour"):
        assert _make_row(status).is_new_or_new_size() is True, status
