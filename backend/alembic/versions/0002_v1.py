from alembic import op
import sqlalchemy as sa
revision="0002_v1"; down_revision="0001_initial"; branch_labels=None; depends_on=None
def upgrade():
    op.add_column("credentials",sa.Column("last_used_at",sa.DateTime(timezone=True)))
    op.add_column("assets",sa.Column("last_scan_status",sa.String(32)))
    op.add_column("assets",sa.Column("inventory_fingerprint",sa.String(64)))
    op.create_index("ix_assets_inventory_fingerprint","assets",["inventory_fingerprint"])
    op.add_column("scans",sa.Column("collectors_ok",sa.Integer(),server_default="0",nullable=False))
    op.add_column("scans",sa.Column("collectors_failed",sa.Integer(),server_default="0",nullable=False))
    op.add_column("software",sa.Column("package_source",sa.String(128)))
    op.drop_constraint("uq_asset_software_identity","software",type_="unique")
    op.create_unique_constraint("uq_asset_software_identity","software",["asset_id","name","source","ecosystem","architecture"])
    op.add_column("inventory_snapshots",sa.Column("fingerprint",sa.String(64),server_default="",nullable=False))
    op.create_index("ix_inventory_snapshots_fingerprint","inventory_snapshots",["fingerprint"])
    op.create_table("audit_events",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False),sa.Column("action",sa.String(128),nullable=False),sa.Column("resource_type",sa.String(64),nullable=False),sa.Column("resource_id",sa.String(128)),sa.Column("outcome",sa.String(32),nullable=False,server_default="success"),sa.Column("details",sa.JSON()))
    op.create_index("ix_audit_events_occurred_at","audit_events",["occurred_at"]); op.create_index("ix_audit_events_action","audit_events",["action"])
def downgrade():
    op.drop_table("audit_events"); op.drop_index("ix_inventory_snapshots_fingerprint",table_name="inventory_snapshots"); op.drop_column("inventory_snapshots","fingerprint"); op.drop_constraint("uq_asset_software_identity","software",type_="unique"); op.create_unique_constraint("uq_asset_software_identity","software",["asset_id","name","source"]); op.drop_column("software","package_source"); op.drop_column("scans","collectors_failed"); op.drop_column("scans","collectors_ok"); op.drop_index("ix_assets_inventory_fingerprint",table_name="assets"); op.drop_column("assets","inventory_fingerprint"); op.drop_column("assets","last_scan_status"); op.drop_column("credentials","last_used_at")
