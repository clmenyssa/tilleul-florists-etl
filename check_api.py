"""How many florists are open in the Rhône today? One request, no key."""
import requests

response = requests.get(
    "https://recherche-entreprises.api.gouv.fr/search",
    params={"activite_principale": "47.76Z", "departement": "69", "etat_administratif": "A", "per_page": 1},
    timeout=30,
)
response.raise_for_status()
print("Florists open in the Rhône today:", response.json()["total_results"])
