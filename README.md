# Tilleul florists ETL

Every week, this pipeline collects the florists of the Rhône from the
[API Recherche d'entreprises](https://recherche-entreprises.api.gouv.fr/docs/),
keeps a raw copy in Amazon S3, and writes the list of prospects in a PostgreSQL
warehouse on Amazon RDS (table `florist_snapshots`, one snapshot per date).

Demo project of the Jedha Data Analytics bootcamp (module Data Ops, days ETL and GitHub Actions).

## Run it on your computer

```bash
cp .env.example .env        # then fill in your values
pip install -r requirements.txt
python etl.py
```

## Run it on GitHub

The workflows are in `.github/workflows/`.
