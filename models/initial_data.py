import re
from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional

from ordered_set import OrderedSet

from models.video import Title, Description
from serializer import DataClassJSONSerializer


@dataclass
class InitItem(DataClassJSONSerializer):
    id: str
    title: Title
    description: Optional[Description] = None
    background_audio: Optional[str] = ""

    @classmethod
    def _post_deserialize_id(cls, obj):
        """
        >>> InitItem._post_deserialize_id(InitItem(id="tt1233333", title=Title(en=""), description=Description(en="")))
        >>> InitItem._post_deserialize_id(InitItem("string", Title(en=""), Description(en="")))
        Traceback (most recent call last):
        AssertionError: Not starting with tt
        """
        assert obj.id.startswith('tt'), "Not starting with tt"

    def title_to_dir(self) -> str:
        return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', self.title.en).lower()


@dataclass
class InitialData(DataClassJSONSerializer):
    """
    >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": {"en":""}, "description": {"en": ""}}, {"id":"tt1233334", "title": {"en":""}, "description": {"en": ""}}], "title": ""})
    InitialData(items=[InitItem(id='tt1233333', title=Title(en='', ru=''), description=Description(ru='', en='')), InitItem(id='tt1233334', title=Title(en='', ru=''), description=Description(ru='', en=''))], title='')
    >>> InitialData.from_json('{"items": [{"id":"tt1233333", "title": {"en":""}, "description": {"en": ""}}, {"id":"tt1233334", "title": {"en":""}, "description": {"en": ""}}], "title": ""}')
    InitialData(items=[InitItem(id='tt1233333', title=Title(en='', ru=''), description=Description(ru='', en='')), InitItem(id='tt1233334', title=Title(en='', ru=''), description=Description(ru='', en=''))], title='')
    """
    items: List[InitItem]
    title: str

    def title_to_dir(self) -> str:
        return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', self.title).lower()

    def ids_items(self) -> List[dict]:
        """
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": {"en":""}, "description": {"en": ""}}, {"id":"tt1233334", "title": {"en": ""}, "description": {"en": ""}}], "title": ""}).ids_items()
        [{'id': 'tt1233333'}, {'id': 'tt1233334'}]
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": {"en":""}, "description": {"en": ""}}], "title": {"en": ""}}).ids_items()
        [{'id': 'tt1233333'}]
        """
        return [{"id": str(item.id)} for item in self.items]

    def ids_to_set(self) -> OrderedSet[str]:
        """
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": {"en": ""}, "description": {"en": ""}}, {"id":"tt1233334", "title": {"en": ""}, "description": {"en": ""}}], "title": ""}).ids_to_set()
        OrderedSet(['tt1233333', 'tt1233334'])
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": {"en": ""}, "description": {"en": ""}}], "title": {"en": ""}}).ids_to_set()
        OrderedSet(['tt1233333'])
        """
        return OrderedSet([item.id for item in self.items])

    @cached_property
    def items_map(self) -> dict:
        return {item.id: item for item in self.items}

    @classmethod
    def items_id_to_query_string(cls, ids: OrderedSet) -> str:
        """
        >>> InitialData.items_id_to_query_string(OrderedSet(["tt1233333", "tt1233334"]))
        '?ids=tt1233333&ids=tt1233334'
        >>> InitialData.items_id_to_query_string(OrderedSet(["tt1233333"]))
        '?ids=tt1233333'
        """
        str_ = "&ids=".join(tuple(map(lambda i: str(i), ids)))
        return f"?ids={str_}"
