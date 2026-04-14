"""
Structured Artifact Generator.
Generates 3 event planning artifacts: Task Checklist, Shopping List, Day-of Schedule.
Each artifact is produced as structured JSON + Markdown for display/download.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any


def generate_fallback_artifact(artifact_type: str, event_context: Dict) -> Dict:
    """Generate a template-based artifact when LLM is unavailable."""
    if artifact_type == "task_checklist":
        return _fallback_checklist(event_context)
    elif artifact_type == "shopping_list":
        return _fallback_shopping_list(event_context)
    elif artifact_type == "day_of_schedule":
        return _fallback_schedule(event_context)
    return {}


def render_artifact_markdown(artifact: Dict) -> str:
    """Convert a structured artifact JSON to human-readable Markdown."""
    atype = artifact.get("artifact_type", "unknown")
    if atype == "task_checklist":
        return _checklist_to_markdown(artifact)
    elif atype == "shopping_list":
        return _shopping_list_to_markdown(artifact)
    elif atype == "day_of_schedule":
        return _schedule_to_markdown(artifact)
    return f"```json\n{json.dumps(artifact, indent=2)}\n```"


# ─────────────────────────────────────────────────────────────────────────────
# Task Checklist
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_checklist(ctx: Dict) -> Dict:
    event_type = ctx.get("event_type", "event")
    event_date = ctx.get("event_date", "TBD")
    guests = ctx.get("guest_count_estimated") or ctx.get("guest_count_confirmed", 20)
    budget = ctx.get("budget_total", 200)
    venue = ctx.get("venue_type", "home")
    dietary = ctx.get("dietary_restrictions", [])
    has_children = ctx.get("has_children", False)

    categories = [
        {
            "name": "4+ Weeks Before",
            "tasks": [
                {
                    "task_id": "t1",
                    "title": "Set date and budget",
                    "description": f"Confirm {event_type} date as {event_date} and finalize ${budget:.0f} budget.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "30 minutes",
                    "priority": "high",
                },
                {
                    "task_id": "t2",
                    "title": "Decide on venue",
                    "description": f"Confirm {venue} as venue. Assess space for {guests} guests.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1 hour",
                    "priority": "high",
                },
                {
                    "task_id": "t3",
                    "title": "Create guest list",
                    "description": f"Finalize guest list of ~{guests} people and collect contact information.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1 hour",
                    "priority": "high",
                },
                {
                    "task_id": "t4",
                    "title": "Send invitations",
                    "description": "Send invitations (digital or physical) with RSVP deadline.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "high",
                },
            ],
        },
        {
            "name": "2–4 Weeks Before",
            "tasks": [
                {
                    "task_id": "t5",
                    "title": "Track RSVPs",
                    "description": "Record responses. Follow up with non-respondents one week before RSVP deadline.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "Ongoing",
                    "priority": "medium",
                },
                {
                    "task_id": "t6",
                    "title": "Plan menu",
                    "description": f"Design menu for {guests} guests"
                    + (f" accommodating: {', '.join(dietary)}" if dietary else "")
                    + ". Decide on appetizers, mains, sides, and desserts.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "high",
                },
                {
                    "task_id": "t7",
                    "title": "Order birthday cake / arrange dessert",
                    "description": "Order cake from bakery (2-week lead time) or plan homemade dessert.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "30 minutes",
                    "priority": "high",
                },
                {
                    "task_id": "t8",
                    "title": "Purchase non-perishable decorations",
                    "description": "Buy balloons, streamers, banner, tablecloths, and other decoration supplies.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "medium",
                },
            ]
            + ([
                {
                    "task_id": "t9",
                    "title": "Plan children's activities",
                    "description": "Prepare age-appropriate games and activities for children attending.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1 hour",
                    "priority": "medium",
                }
            ] if has_children else []),
        },
        {
            "name": "1 Week Before",
            "tasks": [
                {
                    "task_id": "t10",
                    "title": "Confirm final headcount",
                    "description": "Get final RSVP count and adjust food quantities accordingly.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "30 minutes",
                    "priority": "high",
                },
                {
                    "task_id": "t11",
                    "title": "Create detailed shopping list",
                    "description": "Finalize shopping list with exact quantities based on final headcount.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1 hour",
                    "priority": "high",
                },
                {
                    "task_id": "t12",
                    "title": "Create day-of schedule",
                    "description": "Plan minute-by-minute schedule for event day including setup and cleanup.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "45 minutes",
                    "priority": "medium",
                },
                {
                    "task_id": "t13",
                    "title": "Confirm vendor arrangements",
                    "description": "Confirm cake pickup time, any hired entertainment, and delivery arrangements.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "30 minutes",
                    "priority": "high",
                },
            ],
        },
        {
            "name": "Day Before",
            "tasks": [
                {
                    "task_id": "t14",
                    "title": "Grocery shopping (perishables)",
                    "description": "Buy all fresh produce, dairy, meat, and other perishable items.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "high",
                },
                {
                    "task_id": "t15",
                    "title": "Prepare make-ahead dishes",
                    "description": "Cook and refrigerate dishes that can be made in advance.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "2-4 hours",
                    "priority": "high",
                },
                {
                    "task_id": "t16",
                    "title": "Set up decorations (non-food)",
                    "description": "Hang banners, set up table centerpieces, arrange chairs and tables.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "medium",
                },
            ],
        },
        {
            "name": "Day Of",
            "tasks": [
                {
                    "task_id": "t17",
                    "title": "Final food preparation",
                    "description": "Complete cooking, reheat make-ahead dishes, assemble platters.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "high",
                },
                {
                    "task_id": "t18",
                    "title": "Set up food stations",
                    "description": "Arrange food table, set out serving utensils, prepare drinks station with ice.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "30-45 minutes",
                    "priority": "high",
                },
                {
                    "task_id": "t19",
                    "title": "Inflate balloons",
                    "description": "Inflate and arrange balloons for decoration.",
                    "owner": "Host",
                    "status": "pending",
                    "estimated_time": "20-30 minutes",
                    "priority": "low",
                },
                {
                    "task_id": "t20",
                    "title": "Post-event cleanup",
                    "description": "Refrigerate leftovers within 2 hours, clean up, dispose of waste.",
                    "owner": "Host + helpers",
                    "status": "pending",
                    "estimated_time": "1-2 hours",
                    "priority": "medium",
                },
            ],
        },
    ]

    return {
        "artifact_type": "task_checklist",
        "event_title": f"{event_type.title()} — {event_date}",
        "event_date": event_date,
        "generated_at": datetime.now().isoformat(),
        "total_tasks": sum(len(c["tasks"]) for c in categories),
        "completed_tasks": 0,
        "citations": [
            "birthday_party_guide",
            "rsvp_guest_management",
            "catering_guidelines",
            "day_of_schedule_samples",
        ],
        "categories": categories,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Shopping List
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_shopping_list(ctx: Dict) -> Dict:
    event_type = ctx.get("event_type", "event")
    event_date = ctx.get("event_date", "TBD")
    guests = ctx.get("guest_count_estimated") or ctx.get("guest_count_confirmed", 20)
    budget = ctx.get("budget_total", 250.0)
    dietary = ctx.get("dietary_restrictions", [])
    has_children = ctx.get("has_children", False)

    is_vegetarian = "vegetarian" in dietary or "vegan" in dietary
    is_gluten_free = "gluten-free" in dietary

    protein_note = "Plant-based protein option" if is_vegetarian else "Chicken or beef"
    protein_qty = max(1, guests // 4)

    food_items = [
        {
            "item": "Chicken wings / Party protein",
            "quantity": protein_qty,
            "unit": "lbs",
            "estimated_cost": round(protein_qty * 5.5, 2),
            "notes": "6-8 oz per person. " + ("Use plant-based alternative for vegan guests." if is_vegetarian else ""),
        },
        {
            "item": "Salad greens",
            "quantity": max(1, guests // 8),
            "unit": "bags (5 oz each)",
            "estimated_cost": round(max(1, guests // 8) * 3.5, 2),
            "notes": "2-3 oz dressed per person",
        },
        {
            "item": "Bread rolls",
            "quantity": guests + (guests // 5),
            "unit": "rolls",
            "estimated_cost": round((guests + (guests // 5)) * 0.4, 2),
            "notes": "1-2 per person. " + ("Buy certified GF rolls." if is_gluten_free else ""),
        },
        {
            "item": "Potato / pasta side dish",
            "quantity": max(2, guests // 10),
            "unit": "lbs potatoes OR boxes pasta",
            "estimated_cost": round(max(2, guests // 10) * 2.0, 2),
            "notes": "3-4 oz dry pasta per person",
        },
        {
            "item": "Veggie platter (carrots, celery, peppers)",
            "quantity": max(1, guests // 6),
            "unit": "lbs assorted vegetables",
            "estimated_cost": round(max(1, guests // 6) * 3.0, 2),
            "notes": "3-4 oz vegetables per person with dip",
        },
        {
            "item": "Dip (hummus or ranch)",
            "quantity": max(1, guests // 8),
            "unit": "containers (8 oz each)",
            "estimated_cost": round(max(1, guests // 8) * 3.5, 2),
            "notes": "2 tbsp dip per person",
        },
        {
            "item": "Birthday cake",
            "quantity": 1,
            "unit": "9x13 cake (serves ~20-24)",
            "estimated_cost": 35.0,
            "notes": "Bakery sheet cake or homemade. Order 1-2 weeks ahead if from bakery.",
        },
    ]

    if has_children:
        food_items.append({
            "item": "Juice boxes / kids drinks",
            "quantity": max(12, guests // 2),
            "unit": "boxes",
            "estimated_cost": round(max(12, guests // 2) * 0.6, 2),
            "notes": "For children attending",
        })

    bev_items = [
        {
            "item": "Soda (Coke, Sprite, diet)",
            "quantity": max(2, guests // 8),
            "unit": "2-liter bottles",
            "estimated_cost": round(max(2, guests // 8) * 2.5, 2),
            "notes": "Provide variety",
        },
        {
            "item": "Water bottles",
            "quantity": max(1, guests // 12),
            "unit": "24-pack cases",
            "estimated_cost": round(max(1, guests // 12) * 4.5, 2),
            "notes": "1-2 waters per person over event",
        },
        {
            "item": "Ice",
            "quantity": max(2, guests // 10),
            "unit": "10 lb bags",
            "estimated_cost": round(max(2, guests // 10) * 3.5, 2),
            "notes": "Buy day-of. 1-1.5 lbs of ice per guest.",
        },
        {
            "item": "Punch / lemonade mix",
            "quantity": 2,
            "unit": "containers/packets",
            "estimated_cost": 6.0,
            "notes": "Non-alcoholic option for all guests",
        },
    ]

    decor_items = [
        {"item": "Latex balloons", "quantity": 20, "unit": "pack", "estimated_cost": 8.0, "notes": "Variety of colors"},
        {"item": "Streamers", "quantity": 3, "unit": "rolls", "estimated_cost": 6.0, "notes": "Match theme colors"},
        {"item": "Birthday/event banner", "quantity": 1, "unit": "banner", "estimated_cost": 8.0, "notes": "Personalized if possible"},
        {"item": "Tablecloths (plastic)", "quantity": max(2, guests // 10), "unit": "tablecloths", "estimated_cost": round(max(2, guests // 10) * 2.5, 2), "notes": ""},
        {"item": "Candles + lighter", "quantity": 1, "unit": "set", "estimated_cost": 4.0, "notes": "Don't forget these!"},
    ]

    tableware_items = [
        {"item": "Paper/plastic plates", "quantity": round(guests * 1.25), "unit": "plates", "estimated_cost": round(guests * 1.25 * 0.25, 2), "notes": "20% buffer over headcount"},
        {"item": "Cups", "quantity": round(guests * 1.5), "unit": "cups", "estimated_cost": round(guests * 1.5 * 0.15, 2), "notes": "Guests use multiple cups"},
        {"item": "Napkins", "quantity": guests * 3, "unit": "napkins", "estimated_cost": round(guests * 3 * 0.05, 2), "notes": ""},
        {"item": "Plastic cutlery set", "quantity": round(guests * 1.2), "unit": "sets", "estimated_cost": round(guests * 1.2 * 0.2, 2), "notes": "Fork, knife, spoon per guest"},
        {"item": "Garbage bags (large)", "quantity": 5, "unit": "bags", "estimated_cost": 3.5, "notes": "For cleanup"},
    ]

    food_total = sum(i["estimated_cost"] for i in food_items)
    bev_total = sum(i["estimated_cost"] for i in bev_items)
    decor_total = sum(i["estimated_cost"] for i in decor_items)
    tableware_total = sum(i["estimated_cost"] for i in tableware_items)
    total = round(food_total + bev_total + decor_total + tableware_total, 2)

    categories = [
        {"name": "Food", "items": food_items, "subtotal": round(food_total, 2)},
        {"name": "Beverages", "items": bev_items, "subtotal": round(bev_total, 2)},
        {"name": "Decorations", "items": decor_items, "subtotal": round(decor_total, 2)},
        {"name": "Tableware & Supplies", "items": tableware_items, "subtotal": round(tableware_total, 2)},
    ]

    return {
        "artifact_type": "shopping_list",
        "event_title": f"{event_type.title()} — {event_date}",
        "event_date": event_date,
        "generated_at": datetime.now().isoformat(),
        "guest_count": guests,
        "budget_total": budget,
        "budget_allocated": total,
        "budget_remaining": round(budget - total, 2),
        "citations": [
            "shopping_list_templates",
            "catering_guidelines",
            "dietary_guidelines",
            "budget_planning_guide",
        ],
        "categories": categories,
        "total_cost": total,
        "notes": (
            f"Shopping list generated for {guests} guests. "
            + (f"Accommodates: {', '.join(dietary)}. " if dietary else "")
            + ("Budget is tight — consider simplifying menu." if budget and total > budget * 0.9 else "")
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Day-of Schedule
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_schedule(ctx: Dict) -> Dict:
    event_type = ctx.get("event_type", "event")
    event_date = ctx.get("event_date", "TBD")
    event_time = ctx.get("event_time", "15:00")
    duration = ctx.get("event_duration_hours") or 3
    guests = ctx.get("guest_count_estimated") or ctx.get("guest_count_confirmed", 20)
    has_children = ctx.get("has_children", False)

    try:
        from datetime import datetime as dt, timedelta
        start = dt.strptime(event_time, "%H:%M")
    except Exception:
        from datetime import datetime as dt, timedelta
        start = dt.strptime("15:00", "%H:%M")

    def t(base_dt, offset_minutes: int) -> str:
        return (base_dt + timedelta(minutes=offset_minutes)).strftime("%H:%M")

    setup_start = t(start, -120)
    setup_final = t(start, -30)

    setup_blocks = [
        {
            "block_id": "s1",
            "start_time": setup_start,
            "duration_minutes": 60,
            "activity": "Venue setup",
            "responsible": "Host",
            "details": "Set up tables, chairs, decorations, and activity areas.",
            "dependencies": [],
        },
        {
            "block_id": "s2",
            "start_time": t(start, -60),
            "duration_minutes": 30,
            "activity": "Food preparation",
            "responsible": "Host",
            "details": "Final food prep, reheat make-ahead dishes, set up food station.",
            "dependencies": ["s1"],
        },
        {
            "block_id": "s3",
            "start_time": setup_final,
            "duration_minutes": 30,
            "activity": "Final setup",
            "responsible": "Host",
            "details": "Inflate balloons, prepare drinks station with ice, personal readiness.",
            "dependencies": ["s2"],
        },
    ]

    event_blocks = [
        {
            "block_id": "e1",
            "start_time": event_time,
            "duration_minutes": 20,
            "activity": "Guest arrival",
            "responsible": "Host",
            "details": f"Welcome guests as they arrive. Offer welcome drinks immediately.",
            "dependencies": ["s3"],
        },
        {
            "block_id": "e2",
            "start_time": t(start, 20),
            "duration_minutes": 30,
            "activity": "Cocktail hour / mingling",
            "responsible": "Host",
            "details": "Serve appetizers and drinks. Allow guests to socialize.",
            "dependencies": ["e1"],
        },
    ]

    if has_children:
        event_blocks.append({
            "block_id": "e3",
            "start_time": t(start, 50),
            "duration_minutes": 25,
            "activity": "Children's activities / games",
            "responsible": "Host",
            "details": "Run organized games or activities for children.",
            "dependencies": ["e2"],
        })
        next_offset = 75
    else:
        next_offset = 50

    event_blocks.append({
        "block_id": "e4",
        "start_time": t(start, next_offset),
        "duration_minutes": 45,
        "activity": "Main food service",
        "responsible": "Host",
        "details": "Announce food is ready. Serve main dishes and sides.",
        "dependencies": ["e2"],
    })

    event_blocks.append({
        "block_id": "e5",
        "start_time": t(start, next_offset + 45),
        "duration_minutes": 20,
        "activity": "Cake & dessert",
        "responsible": "Host",
        "details": "Bring out birthday cake. Sing Happy Birthday. Cut and serve cake and desserts.",
        "dependencies": ["e4"],
    })

    remaining_minutes = int(duration * 60) - (next_offset + 65)
    if remaining_minutes > 15:
        event_blocks.append({
            "block_id": "e6",
            "start_time": t(start, next_offset + 65),
            "duration_minutes": remaining_minutes - 15,
            "activity": "Free socializing / entertainment",
            "responsible": "Host",
            "details": "Open socializing time, music, optional games.",
            "dependencies": ["e5"],
        })

    end_time_offset = int(duration * 60)
    cleanup_start = t(start, end_time_offset)
    cleanup_blocks = [
        {
            "block_id": "c1",
            "start_time": t(start, end_time_offset - 15),
            "duration_minutes": 15,
            "activity": "Wind down",
            "responsible": "Host",
            "details": "Signal end of event. Distribute party favors if applicable.",
            "dependencies": ["e6" if remaining_minutes > 15 else "e5"],
        },
        {
            "block_id": "c2",
            "start_time": cleanup_start,
            "duration_minutes": 30,
            "activity": "Food cleanup",
            "responsible": "Host + helpers",
            "details": "Refrigerate leftovers within 2 hours of serving. Clear food tables.",
            "dependencies": ["c1"],
        },
        {
            "block_id": "c3",
            "start_time": t(start, end_time_offset + 30),
            "duration_minutes": 60,
            "activity": "Full venue cleanup",
            "responsible": "Host + helpers",
            "details": "Remove decorations, clean tables, sweep/mop, take out garbage.",
            "dependencies": ["c2"],
        },
    ]

    return {
        "artifact_type": "day_of_schedule",
        "event_title": f"{event_type.title()} — {event_date}",
        "event_date": event_date,
        "event_start_time": event_time,
        "event_duration_hours": duration,
        "generated_at": datetime.now().isoformat(),
        "citations": [
            "day_of_schedule_samples",
            "catering_guidelines",
            "birthday_party_guide",
        ],
        "setup_blocks": setup_blocks,
        "event_blocks": event_blocks,
        "cleanup_blocks": cleanup_blocks,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Markdown Renderers
# ─────────────────────────────────────────────────────────────────────────────

def _checklist_to_markdown(artifact: Dict) -> str:
    lines = [
        f"# Task Checklist: {artifact.get('event_title', 'Event')}",
        f"*Generated: {artifact.get('generated_at', '')}*",
        f"*Total tasks: {artifact.get('total_tasks', 0)} | Completed: {artifact.get('completed_tasks', 0)}*",
        "",
        f"**Sources:** {', '.join(artifact.get('citations', []))}",
        "",
    ]
    for cat in artifact.get("categories", []):
        lines.append(f"## {cat['name']}")
        lines.append("")
        lines.append("| # | Task | Owner | Time | Priority | Status |")
        lines.append("|---|------|-------|------|----------|--------|")
        for task in cat.get("tasks", []):
            status_icon = "✅" if task.get("status") == "completed" else "⬜"
            lines.append(
                f"| {status_icon} | **{task['title']}** — {task.get('description', '')} "
                f"| {task.get('owner', '—')} | {task.get('estimated_time', '—')} "
                f"| {task.get('priority', 'medium').upper()} | {task.get('status', 'pending')} |"
            )
        lines.append("")
    return "\n".join(lines)


def _shopping_list_to_markdown(artifact: Dict) -> str:
    lines = [
        f"# Shopping List: {artifact.get('event_title', 'Event')}",
        f"*Generated: {artifact.get('generated_at', '')}*",
        f"*Guests: {artifact.get('guest_count', '?')} | Budget: ${artifact.get('budget_total', 0):.0f} | Estimated Total: ${artifact.get('total_cost', 0):.2f}*",
        "",
        f"**Sources:** {', '.join(artifact.get('citations', []))}",
        "",
    ]
    if artifact.get("budget_remaining", 0) < 0:
        lines.append(f"> ⚠️ **Budget Warning:** Estimated cost ${artifact.get('total_cost', 0):.2f} exceeds budget of ${artifact.get('budget_total', 0):.0f} by ${abs(artifact.get('budget_remaining', 0)):.2f}")
        lines.append("")

    for cat in artifact.get("categories", []):
        lines.append(f"## {cat['name']} (Subtotal: ${cat.get('subtotal', 0):.2f})")
        lines.append("")
        lines.append("| Item | Quantity | Unit | Est. Cost | Notes |")
        lines.append("|------|----------|------|-----------|-------|")
        for item in cat.get("items", []):
            lines.append(
                f"| {item['item']} | {item['quantity']} | {item['unit']} "
                f"| ${item.get('estimated_cost', 0):.2f} | {item.get('notes', '')} |"
            )
        lines.append("")

    lines.append(f"---")
    lines.append(f"**Total Estimated Cost: ${artifact.get('total_cost', 0):.2f}**")
    lines.append(f"**Budget Remaining: ${artifact.get('budget_remaining', 0):.2f}**")
    if artifact.get("notes"):
        lines.append(f"\n*{artifact['notes']}*")
    return "\n".join(lines)


def _schedule_to_markdown(artifact: Dict) -> str:
    lines = [
        f"# Day-Of Schedule: {artifact.get('event_title', 'Event')}",
        f"*Event Date: {artifact.get('event_date', 'TBD')} | Start: {artifact.get('event_start_time', 'TBD')} | Duration: {artifact.get('event_duration_hours', '?')} hours*",
        f"*Generated: {artifact.get('generated_at', '')}*",
        f"*Sources: {', '.join(artifact.get('citations', []))}*",
        "",
    ]

    def render_blocks(title: str, blocks: List[Dict]) -> None:
        if not blocks:
            return
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Time | Duration | Activity | Responsible | Details |")
        lines.append("|------|----------|----------|-------------|---------|")
        for block in blocks:
            lines.append(
                f"| **{block.get('start_time', '?')}** | {block.get('duration_minutes', 0)} min "
                f"| {block.get('activity', '')} | {block.get('responsible', '—')} "
                f"| {block.get('details', '')} |"
            )
        lines.append("")

    render_blocks("🔧 Setup", artifact.get("setup_blocks", []))
    render_blocks("🎉 Event", artifact.get("event_blocks", []))
    render_blocks("🧹 Cleanup", artifact.get("cleanup_blocks", []))

    return "\n".join(lines)
