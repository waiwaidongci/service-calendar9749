// API实体字段约定：来源{id,natural_key,data}、口径{id,version,data}、报告{id,status,snapshot,checksum,result,approved,draft_keys}、计划{next_at,enabled}、发布{id,run_id,idempotency_key,epsilon,result,created,actor}、隐私额度{draft_key,budget,spent}。
export const ENTITY_KEYS=['sources','policies','runs','schedules','deliveries'];
