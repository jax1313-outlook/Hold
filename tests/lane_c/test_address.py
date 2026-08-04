import pytest

from dispatch.receipt.address import JurisdictionDerivationError, derive_jurisdiction


@pytest.mark.parametrize(
    "address,expected",
    [
        ("123 Main St, Amarillo, TX 79101", "TX"),
        ("1 Fuel Plaza, Joplin, MO 64801-1234", "MO"),
        ("Somewhere Rd, Reno, NV", "NV"),
    ],
)
def test_derives_jurisdiction_from_address(address, expected):
    assert derive_jurisdiction(address) == expected


@pytest.mark.parametrize("address", [None, "", "no state info here", "123 Main St"])
def test_raises_rather_than_guessing(address):
    with pytest.raises(JurisdictionDerivationError):
        derive_jurisdiction(address)
