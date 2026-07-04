from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("seeds", "0002_crossreference"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_idea_industry_status_updated "
                "ON seeds_idea (industry_id, status, updated_at DESC);"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_idea_industry_status_updated;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_idea_seed_only_updated "
                "ON seeds_idea (updated_at DESC) WHERE status = 'SEED';"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_idea_seed_only_updated;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_idea_business_only_updated "
                "ON seeds_idea (updated_at DESC) WHERE status = 'BUSINESS';"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_idea_business_only_updated;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_seed_polish_notes_gin "
                "ON seeds_seed USING GIN (polish_notes jsonb_path_ops);"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_seed_polish_notes_gin;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cr_source_score "
                "ON seeds_crossreference (source_business_id, score DESC);"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_cr_source_score;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cr_target_score "
                "ON seeds_crossreference (target_business_id, score DESC);"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_cr_target_score;",
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cr_reltype_source_score "
                "ON seeds_crossreference (relationship_type, source_business_id, score DESC);"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_cr_reltype_source_score;",
        ),
    ]
