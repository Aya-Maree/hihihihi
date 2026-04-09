"""
Spoonacular Food API Integration (Tier 2).
Enriches the shopping list with real recipe-based ingredient information.
"""

import os
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY", "")
BASE_URL = "https://api.spoonacular.com"


async def search_recipes_for_event(event_type: str, dietary_restrictions: List[str], servings: int) -> List[Dict]:
    """
    Search for recipes appropriate for the event type and dietary restrictions.
    Returns list of recipe summaries.
    """
    if not SPOONACULAR_API_KEY:
        return _fallback_recipes(event_type, dietary_restrictions)

    diet = _map_dietary_restrictions(dietary_restrictions)
    query = _get_search_query(event_type)
    number = min(5, max(2, servings // 10))

    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": query,
        "number": number,
        "addRecipeInformation": True,
        "fillIngredients": False,
    }
    if diet:
        params["diet"] = diet

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BASE_URL}/recipes/complexSearch", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            return [
                {
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "servings": r.get("servings", servings),
                    "ready_in_minutes": r.get("readyInMinutes"),
                    "source_url": r.get("sourceUrl"),
                    "image": r.get("image"),
                }
                for r in results
            ]
    except Exception as e:
        print(f"Spoonacular search error: {e}")
        return _fallback_recipes(event_type, dietary_restrictions)


async def get_recipe_ingredients(recipe_id: int, target_servings: int) -> List[Dict]:
    """
    Get scaled ingredient list for a recipe.
    Returns list of ingredient dicts with name, amount, and unit.
    """
    if not SPOONACULAR_API_KEY:
        return []

    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "servings": target_servings,
        "includeNutrition": False,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BASE_URL}/recipes/{recipe_id}/information", params=params)
            resp.raise_for_status()
            data = resp.json()

            ingredients = data.get("extendedIngredients", [])
            return [
                {
                    "name": ing.get("name", ""),
                    "original": ing.get("original", ""),
                    "amount": round(ing.get("amount", 0), 2),
                    "unit": ing.get("unit", ""),
                    "aisle": ing.get("aisle", ""),
                    "estimated_cost": _estimate_ingredient_cost(ing.get("name", ""), ing.get("amount", 0)),
                }
                for ing in ingredients
            ]
    except Exception as e:
        print(f"Spoonacular ingredients error: {e}")
        return []


async def get_ingredient_substitutions(ingredient_name: str) -> List[str]:
    """
    Get substitution suggestions for an ingredient (useful for dietary restrictions).
    """
    if not SPOONACULAR_API_KEY:
        return _fallback_substitutions(ingredient_name)

    params = {"apiKey": SPOONACULAR_API_KEY, "ingredientName": ingredient_name}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BASE_URL}/food/ingredients/substitutes", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("substitutes", [])
    except Exception as e:
        print(f"Spoonacular substitutions error: {e}")
        return _fallback_substitutions(ingredient_name)


async def enrich_shopping_list(
    shopping_list: Dict,
    event_type: str,
    dietary_restrictions: List[str],
    guest_count: int,
) -> Dict:
    """
    Enrich a shopping list with real recipe-based ingredients from Spoonacular.
    Returns the shopping list with an added 'spoonacular_recipes' section.
    """
    recipes = await search_recipes_for_event(event_type, dietary_restrictions, guest_count)

    enriched_ingredients = []
    for recipe in recipes[:3]:
        if recipe.get("id"):
            ingredients = await get_recipe_ingredients(recipe["id"], guest_count)
            if ingredients:
                enriched_ingredients.append({
                    "recipe_title": recipe["title"],
                    "recipe_id": recipe["id"],
                    "servings": guest_count,
                    "source_url": recipe.get("source_url"),
                    "ingredients": ingredients[:15],
                })

    shopping_list["spoonacular_recipes"] = enriched_ingredients
    shopping_list["spoonacular_enriched"] = True

    if enriched_ingredients:
        all_ingredients = [
            ing
            for recipe in enriched_ingredients
            for ing in recipe["ingredients"]
        ]
        recipe_category = {
            "name": "Recipe Ingredients (via Spoonacular)",
            "items": [
                {
                    "item": ing["name"].capitalize(),
                    "quantity": ing["amount"],
                    "unit": ing["unit"] or "units",
                    "estimated_cost": ing.get("estimated_cost", 2.0),
                    "notes": f"For: {ing['original']} | Aisle: {ing.get('aisle', 'general')}",
                }
                for ing in all_ingredients[:20]
            ],
            "subtotal": round(sum(ing.get("estimated_cost", 2.0) for ing in all_ingredients[:20]), 2),
        }
        existing_categories = shopping_list.get("categories", [])
        shopping_list["categories"] = existing_categories + [recipe_category]
        shopping_list["total_cost"] = round(
            sum(cat.get("subtotal", 0) for cat in shopping_list["categories"]), 2
        )

    return shopping_list


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _map_dietary_restrictions(restrictions: List[str]) -> Optional[str]:
    mapping = {
        "vegetarian": "vegetarian",
        "vegan": "vegan",
        "gluten-free": "gluten free",
        "dairy-free": "dairy free",
        "nut-free": "tree nut free",
        "ketogenic": "ketogenic",
        "paleo": "paleo",
    }
    for r in restrictions:
        r_lower = r.lower()
        for key, val in mapping.items():
            if key in r_lower:
                return val
    return None


def _get_search_query(event_type: str) -> str:
    queries = {
        "birthday party": "party finger food appetizers",
        "dinner party": "dinner party main course",
        "holiday gathering": "holiday party food crowd pleaser",
        "graduation party": "graduation party food",
        "baby shower": "baby shower food tea sandwiches",
        "bridal shower": "bridal shower appetizers",
        "anniversary": "romantic anniversary dinner",
        "retirement party": "retirement party food",
    }
    event_lower = event_type.lower()
    for key, query in queries.items():
        if key in event_lower:
            return query
    return "party food appetizers crowd pleaser"


def _estimate_ingredient_cost(name: str, amount: float) -> float:
    """Simple heuristic cost estimation per ingredient."""
    cost_map = {
        "chicken": 4.0, "beef": 5.5, "pork": 4.0, "shrimp": 7.0, "fish": 5.0,
        "pasta": 1.5, "rice": 1.5, "flour": 1.0, "sugar": 1.0,
        "milk": 1.5, "cream": 2.0, "butter": 2.5, "cheese": 3.0, "egg": 0.3,
        "tomato": 1.5, "onion": 1.0, "garlic": 0.5, "pepper": 1.5,
        "olive oil": 2.0, "oil": 1.5, "salt": 0.3, "bread": 2.0,
    }
    name_lower = name.lower()
    for ingredient, base_cost in cost_map.items():
        if ingredient in name_lower:
            return round(base_cost * max(0.5, min(amount, 5) / 2), 2)
    return round(2.0 * max(0.5, min(amount, 3) / 1.5), 2)


def _fallback_recipes(event_type: str, dietary_restrictions: List[str]) -> List[Dict]:
    """Fallback recipes when API key is not available."""
    is_veg = any(r in ["vegetarian", "vegan"] for r in [r.lower() for r in dietary_restrictions])
    recipes = [
        {
            "id": None,
            "title": "Classic Pasta Salad" if is_veg else "Chicken Caesar Salad",
            "servings": 10,
            "ready_in_minutes": 20,
            "source_url": None,
            "image": None,
        },
        {
            "id": None,
            "title": "Hummus & Veggie Platter",
            "servings": 10,
            "ready_in_minutes": 10,
            "source_url": None,
            "image": None,
        },
    ]
    return recipes


def _fallback_substitutions(ingredient: str) -> List[str]:
    substitutions = {
        "butter": ["coconut oil", "vegan butter", "applesauce (in baking)"],
        "milk": ["almond milk", "oat milk", "soy milk", "coconut milk"],
        "eggs": ["flax egg (1 tbsp ground flax + 3 tbsp water)", "chia egg", "applesauce (¼ cup)"],
        "all-purpose flour": ["gluten-free flour blend", "almond flour", "rice flour"],
        "cream": ["coconut cream", "cashew cream", "silken tofu blended"],
    }
    return substitutions.get(ingredient.lower(), [f"Plant-based {ingredient} alternative"])
