"""Regression tests using real Mystic Apparel SS27 order forms - a
different brand/template than the North Kiteboarding fixture, with its own
header wording ("Status" instead of "New / Carry over", "Suggested Retail
Price (Ex VAT)" instead of "Suggested Retail Price"), a leading blank
column in the USD version, and no "Segment" column at all. Exercising this
alongside the North fixture is what catches header-matching regressions
that a single-brand test suite would miss."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from surf_inventory_sync.conversion import run_conversion  # noqa: E402
from surf_inventory_sync.source_parser import filter_new_items, parse_manufacturer_file  # noqa: E402

USD_FIXTURE = Path(__file__).parent / "fixtures" / "sample_mystic_apparel_ss27_usd.xlsx"
EUR_FIXTURE = Path(__file__).parent / "fixtures" / "sample_mystic_apparel_ss27_eur.xlsx"


def test_parses_usd_orderform_despite_leading_blank_column():
    rows = parse_manufacturer_file(USD_FIXTURE)
    assert len(rows) == 669
    # Sanity-check a known row rather than trusting column position alone.
    first = rows[0]
    assert first.item_code == "35101.230102"
    assert first.description == "DTS Rain Jacket"
    assert first.color_description == "Black"
    assert first.size == "S"
    assert first.retail_price == 208.99


def test_parses_eur_orderform_without_leading_blank_column():
    rows = parse_manufacturer_file(EUR_FIXTURE)
    assert len(rows) == 669


def test_status_column_is_recognized_and_filters_correctly_usd():
    rows = parse_manufacturer_file(USD_FIXTURE)
    new_rows = filter_new_items(rows)
    # 'New' + 'New colour'/'New Colour' from the Status column; 'Carry
    # over'/'Carry Over' excluded (observed: 333 + 214 + 1 = 548 new).
    assert len(new_rows) == 548
    assert all("carry" not in (r.status or "").lower() for r in new_rows)


def test_status_column_is_recognized_and_filters_correctly_eur():
    rows = parse_manufacturer_file(EUR_FIXTURE)
    new_rows = filter_new_items(rows)
    assert len(new_rows) == 548


def test_full_conversion_pipeline_on_usd_orderform():
    result = run_conversion(USD_FIXTURE, exchange_rate=3.7, start_item_number=9058)
    assert len(result.new_products) == 548
    assert len(result.rivhit_rows) == 548
    assert result.rivhit_rows[0].rivhit_item_number == 9058
    assert result.rivhit_rows[-1].rivhit_item_number == 9058 + 548 - 1
