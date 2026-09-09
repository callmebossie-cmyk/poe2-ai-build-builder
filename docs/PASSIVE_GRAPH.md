# Passive Graph Rules

Checkpoint 2 uses the real passive nodes and edges imported from the pinned GGG PoE2 passive-tree export.

## Class starts

The source has 12 character-class entries and six shared start nodes. Each start node lists one or more `classStartIndex` values. The importer resolves those indices into the normalized `character_classes` and `class_starts` tables. For example, Ranger and Huntress share node `50459`.

## Traversal rules

- Source edges are treated as undirected allocation connections.
- The source-only virtual node `root` and its edges are excluded. This prevents an invalid shortcut between class starts.
- Ascendancy nodes remain known to the graph but their edges are closed unless that ascendancy ID is explicitly enabled.
- The default graph therefore rejects paths into any ascendancy island.
- An enabled ascendancy graph opens only nodes belonging to the selected ascendancy; other ascendancy islands remain closed.
- Point cost is the number of traversed edges, equivalent to the path length minus the already-owned class start.

## Errors

- An unknown class or node raises `NodeNotFoundError`.
- Known nodes that are disconnected under the current allocation rules raise `PathNotFoundError`.

## Verified real-data example

The nearest projectile passive from the Ranger start is node `56651`, `Projectile Damage`. The path is `50459 -> 56651`, with a point cost of one. The regular-tree connected component reachable from Ranger contains 4,461 nodes at the pinned data revision.
