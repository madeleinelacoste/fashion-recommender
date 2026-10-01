# Data

The raw data is not committed (about 3.5GB).

1. Join the [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations)
   competition on Kaggle and accept its rules.
2. Download these three files into `data/raw/` (the product images are not needed):
   - `transactions_train.csv`
   - `customers.csv`
   - `articles.csv`

   With the Kaggle CLI:

   ```bash
   for f in transactions_train.csv customers.csv articles.csv; do
     kaggle competitions download -c h-and-m-personalized-fashion-recommendations -f $f -p data/raw
   done
   cd data/raw && unzip -o '*.zip' && rm *.zip
   ```

3. Run `python scripts/build_database.py`, which creates `data/hm.duckdb`.
