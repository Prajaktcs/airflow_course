import sys
from airflow.models import DagBag


def test_dag_import():
    """
    Loads all DAGs in the 'dags/' folder. Fails if there's an import error.
    """
    dag_bag = DagBag(dag_folder="dags", include_examples=False)
    if dag_bag.import_errors:
        print("DAG import errors found:")
        for error in dag_bag.import_errors:
            print(error)
        sys.exit(1)
    else:
        print("All DAGs imported successfully!")


if __name__ == "__main__":
    test_dag_import()
