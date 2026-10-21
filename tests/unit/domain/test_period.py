import pytest

from etl.domain.period import Period


def test_period_parse_reads_year_and_month() -> None:
    assert Period.parse("2026-09") == Period(2026, 9)


def test_period_str_is_zero_padded() -> None:
    assert str(Period(2026, 3)) == "2026-03"


def test_period_partition_dir_is_hive_style() -> None:
    assert Period(2026, 9).partition_dir == "period=2026-09"


@pytest.mark.parametrize("text", ["2026-13", "2026-9", "26-09", "abc", ""])
def test_period_parse_rejects_bad_input(text: str) -> None:
    with pytest.raises(ValueError):
        Period.parse(text)


def test_periods_order_chronologically() -> None:
    assert Period(2025, 12) < Period(2026, 1)
