"""The business rules of Tilleul: which florists the sales team may contact."""
import pandas as pd

COLUMNS = {
    "siren": "siren",
    "nom_complet": "name",
    "siege.libelle_commune": "head_office_city",
    "tranche_effectif_salarie": "headcount_band",
    "nombre_etablissements_ouverts": "open_shops",
    "opposition_diffusion_commerciale": "refuses_prospecting",
}
NOT_FLORISTS = "ZOO|ANIMAL|JARDINERIE"


def clean_florists(companies):
    """Turn the raw answer of the API into the list of prospects."""
    table = pd.json_normalize(companies)
    prospects = table[list(COLUMNS)].rename(columns=COLUMNS)
    is_pet_shop = prospects["name"].str.contains(NOT_FLORISTS, case=False)
    refuses = prospects["refuses_prospecting"] == True
    return prospects[~is_pet_shop & ~refuses].drop(columns="refuses_prospecting")
