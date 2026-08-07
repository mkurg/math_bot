from app.core.topics.registry import TopicRegistry
from app.topics.algebraic_expressions import AlgebraicExpressionsModule
from app.topics.invariants import InvariantsModule
from app.topics.numeral_systems import NumeralSystemsModule
from app.topics.times_tables import TimesTablesModule


def main() -> None:
    registry = TopicRegistry()
    registry.register(TimesTablesModule())
    registry.register(NumeralSystemsModule())
    registry.register(InvariantsModule())
    registry.register(AlgebraicExpressionsModule())
    registry.configure(
        ("times_tables", "numeral_systems", "invariants", "algebraic_expressions"),
        "times_tables",
    )
    print(
        "Topic validation passed: times_tables, numeral_systems, invariants, algebraic_expressions"
    )


if __name__ == "__main__":
    main()
