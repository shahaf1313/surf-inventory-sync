"""Orchestrates a full conversion run: manufacturer file -> filtered new
items -> Rivhit rows -> written tab-delimited text file. Kept separate from
the GUI so it can be unit-tested without a display, and reused from a
future CLI/auto-upload path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .rivhit_format import RivhitRow, build_rivhit_rows, write_rivhit_txt
from .source_parser import ProductRow, filter_new_items, parse_manufacturer_file


@dataclass
class ConversionResult:
    all_products: list[ProductRow]
    new_products: list[ProductRow]
    rivhit_rows: list[RivhitRow]
    missing_retail_price: list[ProductRow]  # new items with no retail price - price will be blank

    @property
    def next_item_number(self) -> int:
        """The item number to use as the starting point for the *next* conversion."""
        if not self.rivhit_rows:
            return 0
        return self.rivhit_rows[-1].rivhit_item_number + 1


def run_conversion(
    manufacturer_file: str | Path,
    exchange_rate: float,
    start_item_number: int,
    sheet_names: list[str] | None = None,
) -> ConversionResult:
    all_products = parse_manufacturer_file(manufacturer_file, sheet_names=sheet_names)
    new_products = filter_new_items(all_products)
    rivhit_rows = build_rivhit_rows(new_products, start_id=start_item_number, exchange_rate=exchange_rate)
    missing_price = [p for p in new_products if p.retail_price is None]
    return ConversionResult(
        all_products=all_products,
        new_products=new_products,
        rivhit_rows=rivhit_rows,
        missing_retail_price=missing_price,
    )


def export_to_rivhit_file(result: ConversionResult, output_path: str | Path) -> None:
    write_rivhit_txt(result.rivhit_rows, output_path)
