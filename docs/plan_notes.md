# PostgreSQL Query Plan Notes

## Real Project Table

Query: `SELECT * FROM daily_weather_forecasts WHERE city_id = 'manila';`

- Plan: Sequential Scan
- Estimated rows: 32
- Actual rows: 28
- Rows removed by filter: 252
- Buffers: shared hit=3
- Execution time: 0.091 ms

The Sequential Scan was reasonable because the table was very small:
280 total rows and only 3 cached pages were touched. At this scale,
scanning the table can be cheaper than using an index.

## Synthetic 4M-Row Lab

Table: `plan_lab`

Before indexing `id`:

- Query: `SELECT * FROM plan_lab WHERE id = 42;`
- Plan: Parallel Sequential Scan
- Estimated rows: 2
- Actual rows: 2
- Buffers: shared read=29412
- Execution time: 313.223 ms

After creating `idx_plan_lab_id`:

- Plan: Index Scan
- Estimated rows: 2
- Actual rows: 2
- Buffers: shared hit=3 read=5
- Execution time: 0.104 ms

### City ID Index Observation

For `city_id = 'city_42'`, PostgreSQL changed from a Parallel Seq Scan
to a Bitmap Index Scan + Bitmap Heap Scan after indexing `city_id`.

The speedup was small because the 40,000 matching rows were scattered
across about 29,412 heap pages, so PostgreSQL still had to visit much of
the table.

- Small tables can reasonably use Sequential Scans.
- Index usefulness depends on table size, selectivity, and row distribution.
- `ANALYZE` keeps planner statistics current.
- Estimated rows should be compared with actual rows.
- `BUFFERS` shows how many database pages PostgreSQL had to access.

## Dalibo Visualization

Visualized the indexed `id = 42` plan using explain.dalibo.com.

The plan used an Index Scan on `plan_lab`
with `idx_plan_lab_id`, returning 2 rows as estimated.

Screenshot:
`docs/images/plan_lab_id_index.png`