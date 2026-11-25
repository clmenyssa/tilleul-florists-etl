from cleaning import clean_florists


def company(siren, name, refuses=False):
    return {
        "siren": siren,
        "nom_complet": name,
        "siege": {"libelle_commune": "LYON"},
        "tranche_effectif_salarie": "01",
        "nombre_etablissements_ouverts": 1,
        "opposition_diffusion_commerciale": refuses,
    }


COMPANIES = [
    company("111111111", "LES JARDINS DE FLORE"),
    company("222222222", "MAXI ZOO FRANCE"),
    company("333333333", "ANIMALIS"),
    company("444444444", "FLEURS DU RHONE", refuses=True),
    company("555555555", "L'ATELIER DES FLEURS"),
]


def test_keeps_only_the_prospects():
    prospects = clean_florists(COMPANIES)
    assert list(prospects["siren"]) == ["111111111", "555555555"]


def test_columns_for_the_sales_team():
    prospects = clean_florists(COMPANIES)
    assert list(prospects.columns) == ["siren", "name", "head_office_city", "headcount_band", "open_shops"]
