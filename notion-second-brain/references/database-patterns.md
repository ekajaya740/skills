# Database Patterns

This reference documents the standard database schemas for a Notion second brain.

## Table of Contents

1. [Overview](#overview)
2. [Projects Database](#projects-database)
3. [Tasks Database](#tasks-database)
4. [Notes Database](#notes-database)
5. [Knowledge Database](#knowledge-database)
6. [Areas Database](#areas-database)
7. [Common Property Types](#common-property-types)

---

## Overview

These database schemas form the core of a second brain system. Each database is designed with specific properties to capture essential metadata and enable linking between related entries.

For information about discovering these databases in an existing workspace, see [structure-discovery.md](structure-discovery.md).

---

## Projects Database

Central tracking for projects of any size.

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Name | title | Primary identifier |
| Status | select | Options: Not Started, In Progress, Completed, On Hold |
| Due Date | date | Optional deadline |
| Area | relation | Links to Areas database |
| Tags | multi_select | For categorization |

### Notion DDL

```sql
CREATE TABLE "Projects" (
  "Name" TITLE,
  "Status" SELECT('Not Started', 'In Progress', 'Completed', 'On Hold'),
  "Due Date" DATE,
  "Area" RELATION('areas-database-id'),
  "Tags" MULTI_SELECT()
)
```

---

## Tasks Database

Actionable items that may or may not belong to a project.

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Name | title | Primary identifier |
| Status | select | Options: To Do, In Progress, Done |
| Project | relation | Links to Projects database |
| Due Date | date | Optional deadline |
| Priority | select | Options: Low, Medium, High |

### Notion DDL

```sql
CREATE TABLE "Tasks" (
  "Name" TITLE,
  "Status" SELECT('To Do', 'In Progress', 'Done'),
  "Project" RELATION('projects-database-id'),
  "Due Date" DATE,
  "Priority" SELECT('Low', 'Medium', 'High')
)
```

---

## Notes Database

Ad-hoc notes and quick captures.

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Name | title | Primary identifier |
| Content | rich_text | Note body |
| Tags | multi_select | For categorization |
| Linked Project | relation | Optional project association |

### Notion DDL

```sql
CREATE TABLE "Notes" (
  "Name" TITLE,
  "Content" RICH_TEXT,
  "Tags" MULTI_SELECT(),
  "Linked Project" RELATION('projects-database-id')
)
```

---

## Knowledge Database

Reference material and learnings from external sources.

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Name | title | Primary identifier |
| Summary | rich_text | Brief description |
| Source | url | Original source link |
| Tags | multi_select | For categorization |

### Notion DDL

```sql
CREATE TABLE "Knowledge" (
  "Name" TITLE,
  "Summary" RICH_TEXT,
  "Source" URL,
  "Tags" MULTI_SELECT()
)
```

---

## Areas Database

Broader categories that contain projects, such as work areas or life domains.

### Properties

| Property | Type | Notes |
|----------|------|-------|
| Name | title | Primary identifier |
| Description | rich_text | Area details |
| Status | select | Options: Active, Completed, On Hold |

### Notion DDL

```sql
CREATE TABLE "Areas" (
  "Name" TITLE,
  "Description" RICH_TEXT,
  "Status" SELECT('Active', 'Completed', 'On Hold')
)
```

---

## Common Property Types

### TITLE

Primary text identifier for database entries. Each database must have exactly one title property.

```sql
"Name" TITLE
```

### RICH_TEXT

Long-form text content for descriptions, notes, or body text.

```sql
"Description" RICH_TEXT
```

### SELECT

Single-choice dropdown with predefined options.

```sql
"Status" SELECT('Option A', 'Option B', 'Option C')
```

### MULTI_SELECT

Multiple-choice tags allowing zero or more selections.

```sql
"Tags" MULTI_SELECT()
```

### DATE

Date value with optional time component.

```sql
"Due Date" DATE
```

### RELATION

Link to entries in another database, creating bidirectional connections.

```sql
"Project" RELATION('other-database-id')
```

### URL

Web link to external resources.

```sql
"Source" URL
```

### NUMBER

Numeric values with optional formatting.

```sql
"Count" NUMBER
```

### CHECKBOX

Boolean yes/no flag.

```sql
"Is Complete" CHECKBOX
```

### PEOPLE

Reference to workspace users.

```sql
"Owner" PEOPLE
```

### FILES

File attachments or images.

```sql
"Attachments" FILES
```

---

## Additional Properties

These properties appear less frequently but may be useful:

| Type | Use Case |
|------|----------|
| EMAIL | Contact information |
| PHONE_NUMBER | Contact information |
| UNIQUE_ID | Auto-incrementing identifiers |
| CREATED_TIME | Automatic timestamp |
| LAST_EDITED_TIME | Automatic timestamp |
| ROLLUP | Calculated values from relations |
| FORMULA | Computed properties |

For advanced schema modifications, see the Notion API documentation on database schemas.