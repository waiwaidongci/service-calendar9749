# 临汀服务时窗交付簿

数据服务请求时间→业务时钟核算→站内定时交付；含时区与跨日，非工单客服功能

## 业务场景与工作流
模拟客户：临汀研究协作组，12位业务与分析人员。每月研究明细先从`service-calendar-202611.csv`录入底稿，经口径冻结、Python核算、负责人复核后向业务阅读者交付站内CSV。原有流程依靠人工表格抄算，痛点为口径版本难追溯、重复计算易错、复核与交付脱节。

模块：业务总览、业务底稿、新建口径版本、异步核算与复核、定时交付、站内收件箱、审计、差分隐私发布。底稿可新增/修改/删除；口径仅新增版本；报告提交时冻结来源与版本并保存SHA256。定时交付引用已复核报告快照，worker到期写入数据库，业务阅读者下载。

## 差分隐私外发
同一底稿跨报告反复外发会泄露真实超时数，因此外发一律走差分隐私发布：仅已复核的完成报告可发布，按预先约定的小组（月份×小组×优先级）对冻结结果中每组的超时数与未超时数分别施加拉普拉斯噪声（尺度1/ε），发布的样本数与超时数由加噪计数推出（样本数=加噪超时+加噪未超时），非负与取整为后处理。每份底稿有预先约定的隐私额度（默认总额1.0，每次发布每份底稿消耗0.1，可用DP_BUDGET/DP_EPSILON调整），同一底稿额度跨报告共用；任一底稿余额不足则整份拒发。扣额与可下载结果在同一事务生效，并发发布由账户行锁串行化、唯一约束与CHECK约束兜底，不会透支。发布需客户端携带幂等键；中断后用同一键重试返回原结果且不重复扣额。报告页可发布并下载发布CSV；缺少底稿编号字段的旧报告仅可内部使用，查看、导出与定时交付不受影响。底稿删除不重置额度账户。

## 算法口径
工作日/假日/午休交集分钟与SLA超时分层透视。周五到周一含假日和午休手算；负时段拒绝；边界分钟。

业务时钟 · 午休与假日显式扣除。输入：业务底稿与口径JSON；输出：summary、透视rows、method、warnings。算法实现在`backend/src/services/calculation.py`，输入校验在`validation.py`。固定seed=42，240条合成数据；未对接真实业务系统。修改源数据和新建因子/口径不会改变已提交报告。

## 一天的验收剧本
1. 09:00 admin查看240条seed底稿与具名业务期间。
2. 09:10 analyst添加`service-calendar-202611.csv`的一条具名业务记录。
3. 09:20 admin在口径版本页登记新版本；旧版本保留。
4. 09:30 analyst命名“十一月核算”并选择期间/版本排队。
5. 09:31 Redis worker真实执行Python计算，展示汇总/透视与口径边界。
6. 09:40 admin核对数值后填写至少4字复核说明。
7. 09:45 admin建立60秒周期计划，worker到期生成站内持久化交付。
8. 09:46 viewer在站内收件箱下载交付CSV；审计页查看操作者与时间。
9. 09:50 analyst在报告页发布差分隐私结果并下载发布CSV；同一幂等键重试返回原结果，额度耗尽后整份拒发。

## 快速启动
```sh
cp .env.example .env
docker compose up -d --build
docker compose exec -T backend python -m scripts.seed_demo
```
前端 http://localhost:18252 ，后端 http://localhost:19252/docs ，数据库宿主端口17752。中文父目录可用。恰好5服务frontend/backend/worker/db/redis；均有真实healthcheck。停止并清空演示数据：`docker compose down -v --remove-orphans`。

|角色|邮箱|密码|权限|
|---|---|---|---|
|admin|admin@demo.local|Demo2026!|全部底稿、口径版本、核算、复核、调度|
|analyst|analyst@demo.local|Demo2026!|底稿增改删、核算、导出；无复核/调度/口径写权限|
|viewer|viewer@demo.local|Demo2026!|只读；仅可下载已复核报告与站内交付|

## 工程结构与开发
Python3.11/FastAPI/SQLAlchemy/Redis，PostgreSQL16；前端原生HTML/CSS/JS ES modules，Nginx代理`/api/`剥前缀至后端。`frontend/src`按api/stores/pages/components/hooks/utils/router/constants/types拆分；`backend/src`按models/schemas/services/controllers/routes/middlewares/config/utils/constants拆分；`backend/scripts/seed_demo.py`自然键幂等且不覆盖用户修改。SQLAlchemy启动创建初始结构，迁移说明在backend/migrations。

后端开发：在backend安装requirements，设置DATABASE_URL/REDIS_URL/JWT_SECRET，`uvicorn src.main:app --reload`；前端可用Nginx或带同等代理的静态开发服务器。前后端全部业务计算在Python。

环境变量：COMPOSE_PROJECT_NAME、FRONTEND_PORT、BACKEND_PORT、DB_PORT、JWT_SECRET（部署替换）、DATABASE_URL、REDIS_URL、SEED_DEMO、DP_EPSILON（每次发布每份底稿消耗，默认0.1）、DP_BUDGET（每份底稿预先约定总额度，默认1.0）。`.env`不入Git。数据库/Redis/共享产物为命名卷。共享角色枚举admin/analyst/viewer与状态queued/running/completed/failed分别定义于backend/src/constants/enums.py和frontend/src/constants/enums.js。两个中间件：统一可恢复校验错误、每IP每分钟360请求限流。

## 已知边界
定时分发为站内收件箱；一名worker轮询执行，无外部邮件。调度发送已复核固定报告快照，不自动重算新数据。时间显示Asia/Shanghai。报告导出适合小型数据；底稿全量加载240行演示数据。Google Fonts不可用时回退serif。后端API以专属字段对象收发，页面通过业务输入控件编辑，不要求用户写JSON。新增来源期间自动可选；专属字段和算法严格校验。JWT演示有效期2小时。

MIT License。

## 实际实体映射
来源记录（Source，专属业务字段校验）、口径版本（Policy）、核算报告（Run）、交付计划（Schedule）、交付（Delivery）均经数据库→模型→请求schema→service→route/controller→frontend API→store→page。Period为已有来源期间字典，在任务期间选择器使用；不单独作为复杂度计数。底稿JSON为小型多字段单记录存储，不虚构未落库的子实体。

实际表：期间字典 service_periods；专属来源 service_cases；冻结口径 business_calendars；异步报告 sla_runs；底稿隐私额度 privacy_accounts；差分隐私发布 dp_publications。
