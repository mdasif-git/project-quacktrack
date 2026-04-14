from dagster_duckdb import DuckDBResource
import dagster as dg


db_res = DuckDBResource(
    database="D:\\projects\\project-quacktrack\\data\\duck_db\\expenses_transactions.db"
)

@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={
        'duckdb': db_res
    })
