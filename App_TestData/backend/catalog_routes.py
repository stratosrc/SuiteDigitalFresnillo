from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from App_TestData.data.catalogue_data import CATALOGUE_SECTIONS, build_catalogue_categories, build_catalogue_items

router = APIRouter(prefix="/api")


@router.get("/catalogo")
def catalogue() -> JSONResponse:
    all_items = build_catalogue_items()
    item_ids_by_name = {name: item_id for item_id, name in all_items}
    return JSONResponse(
        {
            "items": [{"id": concept_id, "name": name} for concept_id, name in all_items],
            "categories": build_catalogue_categories(),
            "sections": [
                {
                    "title": title,
                    "items": [
                        {"id": item_ids_by_name.get(item_name, index), "name": item_name}
                        for index, item_name in enumerate(section_items, start=1)
                    ],
                }
                for title, section_items in CATALOGUE_SECTIONS
            ],
        }
    )
