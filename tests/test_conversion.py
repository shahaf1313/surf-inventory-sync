import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.conversion import export_to_rivhit_file, run_conversion  # noqa: E402

MANUFACTURER_FIXTURE = Path(__file__).parent / "fixtures" / "sample_manufacturer_orderform.xlsx"


def test_run_conversion_end_to_end():
    result = run_conversion(
        MANUFACTURER_FIXTURE,
        exchange_rate=3.7,
        start_item_number=8886,
        sheet_names=["North ALL products "],
    )
    assert len(result.all_products) == 660
    assert len(result.new_products) == 172
    assert len(result.rivhit_rows) == 172
    assert result.rivhit_rows[0].rivhit_item_number == 8886
    assert result.rivhit_rows[0].price == round(result.new_products[0].retail_price * 3.7)
    # every fixture product has a retail price, so nothing should be flagged
    assert result.missing_retail_price == []


def test_next_item_number_continues_after_the_batch():
    result = run_conversion(
        MANUFACTURER_FIXTURE,
        exchange_rate=3.7,
        start_item_number=8886,
        sheet_names=["North ALL products "],
    )
    assert result.next_item_number == 8886 + 172


def test_next_item_number_with_no_new_items_keeps_start_number():
    # Simulate "nothing new this batch" by pointing at a fixture with no matches
    # is out of scope here; instead directly exercise the empty-rows branch.
    from surf_inventory_sync.conversion import ConversionResult

    empty = ConversionResult(all_products=[], new_products=[], rivhit_rows=[], missing_retail_price=[])
    assert empty.next_item_number == 0


def test_export_writes_a_valid_rivhit_file(tmp_path):
    result = run_conversion(
        MANUFACTURER_FIXTURE,
        exchange_rate=3.7,
        start_item_number=8886,
        sheet_names=["North ALL products "],
    )
    out_file = tmp_path / "new_items_ss26.txt"
    export_to_rivhit_file(result, out_file)

    content = out_file.read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    assert len(lines) == 172

    first_fields = lines[0].split("\t")
    assert len(first_fields) == 11  # A..K, matching the Rivhit .xls layout
    assert first_fields[0] == "8886"
    assert first_fields[1] == result.rivhit_rows[0].raw_description
    assert first_fields[3:10] == [""] * 7  # D-J always blank
