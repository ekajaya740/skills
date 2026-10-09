# draw.io ERD Template Reference

This is a condensed template for a draw.io ERD XML. It shows one table + one relationship — extend the pattern for any schema size.

## Minimal file structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram name="ERD" id="solo-erd">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10"
      pageWidth="1400" pageHeight="1100" background="#0a0a1a">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- All vertices and edges go here, parent=1 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Table entity pattern

```xml
<!-- === TABLE: users (Core entity) === -->
<mxCell id="t-users" value="users" style="rounded=1;whiteSpace=wrap;html=1;
  fillColor=#12122a;strokeColor=#f59e0b;strokeWidth=2;fontColor=#f59e0b;
  fontStyle=1;fontSize=12;" parent="1" vertex="1">
  <mxGeometry x="50" y="170" width="280" height="160" as="geometry"/>
</mxCell>

<!-- PK column -->
<mxCell id="t-users-id" value="🔑 id (INT PK)" style="text;html=1;
  strokeColor=none;fillColor=none;fontColor=#e2e8f0;fontSize=10;"
  parent="1" vertex="1">
  <mxGeometry x="60" y="195" width="260" height="18" as="geometry"/>
</mxCell>

<!-- Regular column -->
<mxCell id="t-users-name" value="name (TEXT)" style="text;html=1;
  strokeColor=none;fillColor=none;fontColor=#e2e8f0;fontSize=10;"
  parent="1" vertex="1">
  <mxGeometry x="60" y="213" width="260" height="18" as="geometry"/>
</mxCell>

<!-- FK column -->
<mxCell id="t-users-role" value="🔗 role_id (INT FK → roles)" style="text;html=1;
  strokeColor=none;fillColor=none;fontColor=#e2e8f0;fontSize=10;"
  parent="1" vertex="1">
  <mxGeometry x="60" y="231" width="260" height="18" as="geometry"/>
</mxCell>

<!-- Muted/optional column -->
<mxCell id="t-users-ts" value="created_at (TIMESTAMP)" style="text;html=1;
  strokeColor=none;fillColor=none;fontColor=#94a3b8;fontSize=10;"
  parent="1" vertex="1">
  <mxGeometry x="60" y="249" width="260" height="18" as="geometry"/>
</mxCell>
```

### Column offset calculation

Table header at `y`, columns start at `y+25`, each subsequent column adds `18`:
```
row 0: y + 25   (first column)
row 1: y + 43
row 2: y + 61
...
row N: y + 25 + (N * 18)
```

## Relationship (FK) edge pattern

```xml
<!-- users → orders (1:*) -->
<mxCell id="rel-users-orders" value="" style="endArrow=classic;startArrow=classic;
  html=1;rounded=0;strokeColor=#8b5cf6;" parent="1" edge="1"
  source="t-orders" target="t-users">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

For explicit anchor points:
```xml
<mxCell id="rel-fk" value="" style="..." parent="1" edge="1"
  source="t-orders" target="t-users">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="420" y="250" as="sourcePoint"/>
    <mxPoint x="330" y="250" as="targetPoint"/>
  </mxGeometry>
</mxCell>
```

## Color scheme (dark theme)

| Role | Fill | Stroke | Font (header) |
|---|---|---|---|
| Core entity | `#12122a` | `#f59e0b` | `#f59e0b` |
| Recurring / habits | `#12122a` | `#10b981` | `#10b981` |
| Transaction log | `#12122a` | `#3b82f6` | `#3b82f6` |
| Join / mapping | `#12122a` | `#8b5cf6` | `#8b5cf6` |
| Failure / misses | `#12122a` | `#ef4444` | `#ef4444` |
| Metadata / system | `#12122a` | `#94a3b8` | `#94a3b8` |

Column text: `#e2e8f0` (regular), `#94a3b8` (muted/optional)

## Legend pattern

```xml
<mxCell id="legend" value="🔑 Primary Key" style="text;html=1;strokeColor=none;
  fillColor=none;fontColor=#f59e0b;fontSize=11;" parent="1" vertex="1">
  <mxGeometry x="65" y="45" width="180" height="20" as="geometry"/>
</mxCell>
<mxCell id="legend-fk" value="🔗 Foreign Key" style="text;html=1;strokeColor=none;
  fillColor=none;fontColor=#8b5cf6;fontSize=11;" parent="1" vertex="1">
  <mxGeometry x="65" y="70" width="180" height="20" as="geometry"/>
</mxCell>
```

## Embed page (Astro example)

```astro
---
import Layout from '../layouts/Layout.astro';
---
<Layout title="ERD">
  <h1>Database ERD</h1>
  <a href="https://app.diagrams.net/#Uyour.domain.com%2Ferd%2Fer.drawio"
     target="_blank">✏️ Edit in draw.io</a>
  <iframe
    src="https://viewer.diagrams.net/?embed=1&ui=min&spin=1&proto=json
      &highlight=0000ff&nav=1&title=ERD
      #Uhttps%3A%2F%2Fyour.domain.com%2Ferd%2Fer.drawio"
    style="width:100%;height:800px;border:none;"
    allowfullscreen>
  </iframe>
</Layout>
```
