"""Check that the YouTube Music authentication headers work."""

from .ytmusic_client import _get_client


def main() -> None:
    account = _get_client().get_account_info()
    print(f"Authenticated as: {account.get('accountName', 'unknown')}")


if __name__ == "__main__":
    main()
