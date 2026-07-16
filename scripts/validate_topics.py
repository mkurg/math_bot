from app.core.topics.registry import TopicRegistry
from app.topics.numeral_systems import NumeralSystemsModule
from app.topics.times_tables import TimesTablesModule


def main() -> None:
    registry = TopicRegistry()
    registry.register(TimesTablesModule())
    registry.register(NumeralSystemsModule())
    registry.configure(("times_tables", "numeral_systems"), "times_tables")
    print("Topic validation passed: times_tables, numeral_systems")


if __name__ == "__main__":
    main()
