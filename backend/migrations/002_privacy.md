# 002 差分隐私发布

新增表（SQLAlchemy 启动时 create_all 自动建立）：

- `privacy_accounts`：底稿隐私额度账户。`draft_key`（底稿编号，唯一）、`budget`（预先约定的总额度 ε）、`spent`（已消耗 ε）。约束 `spent<=budget`，数据库层面兜底防透支；底稿删除不重置账户。
- `dp_publications`：差分隐私发布记录。`run_id`、`idempotency_key`（幂等键，唯一）、`epsilon`（本次每份底稿消耗）、`result`（加噪后冻结结果）、`created`、`actor`。

变更列：

- `sla_runs` 新增 `draft_keys JSON`（报告冻结的底稿编号列表）。应用启动时自动执行
  `ALTER TABLE sla_runs ADD COLUMN IF NOT EXISTS draft_keys JSON`（PostgreSQL）。
  旧行保持 `NULL`：缺少底稿编号字段的旧报告仅可内部使用（查看、导出、定时交付不变），不可对外发布。

扣额与发布记录在同一事务提交；并发发布由 `privacy_accounts` 行锁（按底稿编号排序加锁）串行化，唯一约束与 CHECK 约束兜底。升级前请备份数据库。
