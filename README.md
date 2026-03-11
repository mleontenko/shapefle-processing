poetry run python -m shapefile_processing

poetry run python src/shapefile_processing/__main__.py

poetry run python -m unittest

poetry run python -m unittest discover -s tests -p "test_*.py" -v