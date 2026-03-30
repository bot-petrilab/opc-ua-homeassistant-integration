from __future__ import annotations

from collections import deque
from typing import Any


async def read_single_node_value(client, node_id: str) -> Any:
    """Read a single node value from an asyncua client."""
    node = client.get_node(node_id)
    return await node.read_value()


async def read_node_batch(client, node_ids: list[str], logger, endpoint: str) -> dict[str, Any]:
    """Read a batch of nodes, keeping partial successes."""
    results: dict[str, Any] = {}
    for node_id in node_ids:
        try:
            results[node_id] = await read_single_node_value(client, node_id)
        except Exception as err:
            logger.debug(
                "Read failed for node %s on %s: %s",
                node_id,
                endpoint,
                err,
            )
    return results


async def browse_collect_child_rows(node, queue, rows, seen, max_nodes: int) -> None:
    """Queue children for breadth-first browse traversal."""
    children = await node.get_children()
    for child in children:
        if len(rows) >= max_nodes:
            break
        nodeid_obj = child.nodeid
        node_id = nodeid_obj.to_string() if hasattr(nodeid_obj, "to_string") else str(nodeid_obj)
        if node_id in seen:
            continue
        seen.add(node_id)
        queue.append(child)


async def browse_nodes(client, root_node_id: str, depth: int = 2, max_nodes: int = 200) -> list[dict[str, Any]]:
    """Browse a subtree and return serializable node metadata."""
    root = client.get_node(root_node_id)
    queue: deque[tuple[Any, int, str | None]] = deque([(root, 0, None)])
    rows: list[dict[str, Any]] = []
    seen = {root_node_id}

    while queue and len(rows) < max_nodes:
        node, level, parent_node_id = queue.popleft()
        nodeid_obj = node.nodeid
        node_id = nodeid_obj.to_string() if hasattr(nodeid_obj, "to_string") else str(nodeid_obj)

        browse_name = await node.read_browse_name()
        display_name = await node.read_display_name()
        node_class_obj = await node.read_node_class()
        node_class = getattr(node_class_obj, "name", str(node_class_obj))

        row: dict[str, Any] = {
            "node_id": node_id,
            "parent_node_id": parent_node_id,
            "name": getattr(display_name, "Text", None)
            or getattr(browse_name, "Name", None)
            or node_id,
            "browse_name": getattr(browse_name, "Name", None),
            "node_class": node_class,
            "level": level,
        }

        try:
            path = await node.get_path(as_string=True)
            row["path"] = "/".join(path)
        except Exception:
            row["path"] = None

        if node_class == "Variable":
            try:
                value = await node.read_value()
                row["sample_type"] = type(value).__name__
            except Exception:
                row["sample_type"] = None
            try:
                row["is_writable"] = await node.get_writable()
            except Exception:
                row["is_writable"] = False
        else:
            row["sample_type"] = None
            row["is_writable"] = False
            try:
                type_definition = await node.read_type_definition()
                if type_definition is not None:
                    td_obj = getattr(type_definition, "nodeid", type_definition)
                    row["type_definition"] = (
                        td_obj.to_string() if hasattr(td_obj, "to_string") else str(td_obj)
                    )
            except Exception:
                row["type_definition"] = None

        rows.append(row)

        if level < depth:
            await browse_collect_child_rows(node, queue, rows, seen, max_nodes)

    return rows
