"""
Spoonacular Food API Integration (Tier 2).
Enriches the shopping list with real recipe-based ingredient information.
"""

import os
import random
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
    # Request more results than needed so we can randomly sample for variety
    fetch_count = 20

    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "query": query,
        "number": fetch_count,
        "addRecipeInformation": True,
        "fillIngredients": False,
        "offset": random.randint(0, 10),  # Random offset for extra variety
    }
    if diet:
        params["diet"] = diet

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BASE_URL}/recipes/complexSearch", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return _fallback_recipes(event_type, dietary_restrictions)
            # Randomly pick 2-3 from the pool for variety each time
            pick = min(3, max(2, servings // 10))
            selected = random.sample(results, min(pick, len(results)))
            return [
                {
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "servings": r.get("servings", servings),
                    "ready_in_minutes": r.get("readyInMinutes"),
                    "source_url": r.get("sourceUrl"),
                    "image": r.get("image"),
                }
                for r in selected
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
            # Real Spoonacular recipe — fetch full ingredient list
            ingredients = await get_recipe_ingredients(recipe["id"], guest_count)
            if ingredients:
                enriched_ingredients.append({
                    "recipe_title": recipe["title"],
                    "recipe_id": recipe["id"],
                    "servings": guest_count,
                    "source_url": recipe.get("source_url"),
                    "ingredients": ingredients[:15],
                })
        elif recipe.get("fallback_ingredients"):
            # Fallback recipe with pre-baked ingredient list
            enriched_ingredients.append({
                "recipe_title": recipe["title"],
                "recipe_id": None,
                "servings": guest_count,
                "source_url": recipe.get("source_url"),
                "ingredients": recipe["fallback_ingredients"],
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
        "birthday party": "cake dessert",
        "dinner party": "pasta chicken dinner",
        "holiday gathering": "roast turkey stuffing",
        "graduation party": "sandwiches salad",
        "baby shower": "finger food sandwiches",
        "bridal shower": "salad appetizer",
        "anniversary": "chicken dinner romantic",
        "retirement party": "buffet salad",
    }
    event_lower = event_type.lower()
    for key, query in queries.items():
        if key in event_lower:
            return query
    return "chicken salad pasta"


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
    """Fallback recipes with pre-baked ingredients when API key is not available."""
    is_veg = any(r in ["vegetarian", "vegan"] for r in [r.lower() for r in dietary_restrictions])
    is_gf  = any("gluten" in r.lower() for r in dietary_restrictions)

    recipes = []

    # Main dish
    if is_veg:
        recipes.append({
            "id": None,
            "title": "Classic Pasta Salad (Vegetarian)",
            "servings": 10,
            "ready_in_minutes": 25,
            "source_url": None,
            "image": None,
            "fallback_ingredients": [
                {"name": "rotini pasta", "original": "500g rotini pasta", "amount": 500, "unit": "g", "aisle": "Pasta & Rice", "estimated_cost": 2.50},
                {"name": "cherry tomatoes", "original": "2 cups cherry tomatoes", "amount": 2, "unit": "cups", "aisle": "Produce", "estimated_cost": 3.00},
                {"name": "cucumber", "original": "1 large cucumber, diced", "amount": 1, "unit": "whole", "aisle": "Produce", "estimated_cost": 1.50},
                {"name": "bell pepper", "original": "2 bell peppers, diced", "amount": 2, "unit": "whole", "aisle": "Produce", "estimated_cost": 2.00},
                {"name": "black olives", "original": "1 can black olives", "amount": 1, "unit": "can", "aisle": "Canned Goods", "estimated_cost": 1.80},
                {"name": "feta cheese", "original": "200g feta cheese", "amount": 200, "unit": "g", "aisle": "Dairy", "estimated_cost": 3.50},
                {"name": "Italian dressing", "original": "1 bottle Italian dressing", "amount": 1, "unit": "bottle", "aisle": "Condiments", "estimated_cost": 2.50},
            ],
        })
    else:
        recipes.append({
            "id": None,
            "title": "Chicken Caesar Salad",
            "servings": 10,
            "ready_in_minutes": 30,
            "source_url": None,
            "image": None,
            "fallback_ingredients": [
                {"name": "chicken breast", "original": "1.5 kg chicken breast", "amount": 1.5, "unit": "kg", "aisle": "Meat", "estimated_cost": 12.00},
                {"name": "romaine lettuce", "original": "3 heads romaine lettuce", "amount": 3, "unit": "heads", "aisle": "Produce", "estimated_cost": 4.50},
                {"name": "parmesan cheese", "original": "150g parmesan, shaved", "amount": 150, "unit": "g", "aisle": "Dairy", "estimated_cost": 4.00},
                {"name": "Caesar dressing", "original": "1 bottle Caesar dressing", "amount": 1, "unit": "bottle", "aisle": "Condiments", "estimated_cost": 3.00},
                {"name": "croutons", "original": "2 cups croutons", "amount": 2, "unit": "cups", "aisle": "Bread", "estimated_cost": 2.00},
                {"name": "lemon", "original": "2 lemons for dressing", "amount": 2, "unit": "whole", "aisle": "Produce", "estimated_cost": 1.00},
            ],
        })

    # Appetizer — works for most events
    recipes.append({
        "id": None,
        "title": "Hummus & Veggie Platter",
        "servings": 10,
        "ready_in_minutes": 10,
        "source_url": None,
        "image": None,
        "fallback_ingredients": [
            {"name": "hummus", "original": "2 large tubs hummus (400g each)", "amount": 2, "unit": "tubs", "aisle": "Deli", "estimated_cost": 6.00},
            {"name": "baby carrots", "original": "300g baby carrots", "amount": 300, "unit": "g", "aisle": "Produce", "estimated_cost": 2.00},
            {"name": "celery", "original": "1 bunch celery, cut into sticks", "amount": 1, "unit": "bunch", "aisle": "Produce", "estimated_cost": 1.50},
            {"name": "cucumber", "original": "2 cucumbers, sliced", "amount": 2, "unit": "whole", "aisle": "Produce", "estimated_cost": 2.00},
            {"name": "pita bread", "original": "2 packs pita bread" if not is_gf else "2 packs gluten-free crackers", "amount": 2, "unit": "packs", "aisle": "Bread", "estimated_cost": 3.50},
            {"name": "cherry tomatoes", "original": "1 pint cherry tomatoes", "amount": 1, "unit": "pint", "aisle": "Produce", "estimated_cost": 2.50},
        ],
    })

    # Dessert
    recipes.append({
        "id": None,
        "title": "Chocolate Brownie Bites",
        "servings": 10,
        "ready_in_minutes": 40,
        "source_url": None,
        "image": None,
        "fallback_ingredients": [
            {"name": "butter", "original": "200g unsalted butter", "amount": 200, "unit": "g", "aisle": "Dairy", "estimated_cost": 2.50},
            {"name": "dark chocolate", "original": "300g dark chocolate chips", "amount": 300, "unit": "g", "aisle": "Baking", "estimated_cost": 4.00},
            {"name": "eggs", "original": "4 large eggs", "amount": 4, "unit": "whole", "aisle": "Dairy", "estimated_cost": 1.50},
            {"name": "sugar", "original": "250g sugar", "amount": 250, "unit": "g", "aisle": "Baking", "estimated_cost": 1.00},
            {"name": "all-purpose flour", "original": "120g flour" if not is_gf else "120g gluten-free flour", "amount": 120, "unit": "g", "aisle": "Baking", "estimated_cost": 0.80},
            {"name": "vanilla extract", "original": "1 tsp vanilla extract", "amount": 1, "unit": "tsp", "aisle": "Baking", "estimated_cost": 0.50},
        ],
    })

    random.shuffle(recipes)
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
