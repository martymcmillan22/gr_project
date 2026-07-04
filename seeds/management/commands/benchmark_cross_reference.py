import json

from django.core.management.base import BaseCommand
from django.db import connection


BENCHMARK_QUERIES = {
    "q1": """
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT target_business_id, relationship_type, score
        FROM seeds_crossreference
        WHERE source_business_id = %(source_business_id)s
        ORDER BY score DESC
        LIMIT 100
    """,
    "q2": """
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT source_business_id, relationship_type, score
        FROM seeds_crossreference
        WHERE target_business_id = %(target_business_id)s
        ORDER BY score DESC
        LIMIT 100
    """,
    "q3": """
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT target_business_id, score
        FROM seeds_crossreference
        WHERE relationship_type = %(relationship_type)s
          AND source_business_id = %(source_business_id)s
        ORDER BY score DESC
        LIMIT 100
    """,
}


class Command(BaseCommand):
    help = "Run EXPLAIN ANALYZE benchmark queries for cross-reference read paths."

    def add_arguments(self, parser):
        parser.add_argument("--query", choices=BENCHMARK_QUERIES.keys(), default="q1")
        parser.add_argument("--source-business-id", type=int, default=1)
        parser.add_argument("--target-business-id", type=int, default=1)
        parser.add_argument("--relationship-type", type=str, default="similar")

    def handle(self, *args, **options):
        query_key = options["query"]
        query_sql = BENCHMARK_QUERIES[query_key]
        params = {
            "source_business_id": options["source_business_id"],
            "target_business_id": options["target_business_id"],
            "relationship_type": options["relationship_type"],
        }

        with connection.cursor() as cursor:
            cursor.execute(query_sql, params)
            raw_plan = cursor.fetchone()[0][0]

        summary = {
            "query": query_key,
            "execution_time_ms": raw_plan.get("Execution Time"),
            "planning_time_ms": raw_plan.get("Planning Time"),
            "shared_hit_blocks": raw_plan.get("Plan", {}).get("Shared Hit Blocks"),
            "shared_read_blocks": raw_plan.get("Plan", {}).get("Shared Read Blocks"),
            "plan_node_type": raw_plan.get("Plan", {}).get("Node Type"),
        }

        self.stdout.write(self.style.SUCCESS("Benchmark Summary"))
        self.stdout.write(json.dumps(summary, indent=2))
