"""Print the page credit balance and the Parser Templates in the account."""

from parserbee import ParserBee


def main() -> None:
    with ParserBee() as client:
        credits = client.get_credits()
        print(f"Plan: {credits['subscription_plan']} ({credits['subscription_status']})")
        print(f"Page credits: {credits['credits_remaining']} of {credits['credits_total']}")

        print("\nParser Templates:")
        for template in client.list_templates():
            print(f"  {template['id']}  {template['name']}")


if __name__ == "__main__":
    main()
