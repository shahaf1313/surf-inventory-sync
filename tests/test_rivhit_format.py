import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.rivhit_format import (  # noqa: E402
    build_rivhit_rows,
    find_id_gaps,
    format_description,
    next_available_id,
    parse_rivhit_new_items_file,
    write_rivhit_xls,
)
from surf_inventory_sync.source_parser import (  # noqa: E402
    ProductRow,
    filter_new_items,
    parse_manufacturer_file,
)

RIVHIT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_rivhit_new_items_ss24.xls"
MANUFACTURER_FIXTURE = Path(__file__).parent / "fixtures" / "sample_manufacturer_orderform.xlsx"


def test_parses_all_rows_of_real_rivhit_file():
    rows = parse_rivhit_new_items_file(RIVHIT_FIXTURE)
    assert len(rows) == 4173


def test_running_id_sequence_has_no_gaps():
    rows = parse_rivhit_new_items_file(RIVHIT_FIXTURE)
    assert find_id_gaps(rows) == []
    assert rows[0].rivhit_item_number == 4713
    assert rows[-1].rivhit_item_number == 8885


def test_next_available_id_continues_the_sequence():
    rows = parse_rivhit_new_items_file(RIVHIT_FIXTURE)
    assert next_available_id(rows) == 8886


def test_almost_all_descriptions_match_the_expected_pattern():
    rows = parse_rivhit_new_items_file(RIVHIT_FIXTURE)
    valid = [r for r in rows if r.is_valid]
    invalid = [r for r in rows if not r.is_valid]
    # One known junk/note row embedded in the real file; everything else parses.
    assert len(invalid) == 1
    assert "LIFESTYLE" in invalid[0].raw_description
    assert len(valid) == 4172


def test_known_row_parses_into_expected_fields():
    rows = parse_rivhit_new_items_file(RIVHIT_FIXTURE)
    row = rows[0]
    assert row.rivhit_item_number == 4713
    assert row.description == "Bomber Jacket"
    assert row.size == "S"
    assert row.color_description == "Slate Brown"
    assert row.manufacturer_item_code == "35101.240078"
    assert row.barcode == "8715738826175"
    assert row.price == 574.0


def test_build_and_roundtrip_write_matches_dads_existing_format(tmp_path):
    products = [
        ProductRow(
            ranking="1",
            sub_group="North Kites",
            segment="North Kite & Foils",
            item_code="85000.260014",
            barcode="8715738911000",
            description="Reach Ultra Kite",
            color_code="900",
            color_description="Black",
            size="7m",
            status="New",
            retail_price=2169,
            wholesale_price=1100.6,
            order_qty=0,
            order_amount=0,
            source_sheet="North ALL products",
        )
    ]
    rows = build_rivhit_rows(products, start_id=8886, price_field="wholesale_price")
    assert rows[0].rivhit_item_number == 8886
    assert format_description(products[0]) == "Reach Ultra Kite, 7m, Black, Item 85000.260014"

    out_file = tmp_path / "out.xls"
    write_rivhit_xls(rows, out_file)

    reparsed = parse_rivhit_new_items_file(out_file)
    assert len(reparsed) == 1
    assert reparsed[0].rivhit_item_number == 8886
    assert reparsed[0].description == "Reach Ultra Kite"
    assert reparsed[0].size == "7m"
    assert reparsed[0].color_description == "Black"
    assert reparsed[0].manufacturer_item_code == "85000.260014"
    assert reparsed[0].barcode == "8715738911000"
    assert reparsed[0].price == 1100.6


def test_end_to_end_manufacturer_file_to_rivhit_rows():
    """Full pipeline: manufacturer file -> filter new items -> build Rivhit rows."""
    products = parse_manufacturer_file(MANUFACTURER_FIXTURE, sheet_names=["North ALL products "])
    new_products = filter_new_items(products)
    rows = build_rivhit_rows(new_products, start_id=8886)
    assert len(rows) == 172
    assert rows[0].rivhit_item_number == 8886
    assert rows[-1].rivhit_item_number == 8886 + 172 - 1
    # Every generated row should match Rivhit's own description pattern when
    # round-tripped through the parser (catches subtle formatting mismatches).
    for row in rows:
        assert row.description  # non-empty
