SET NAMES utf8mb4;

USE opendataworks;

-- Use a narrow demo datasource config so Data Studio screenshots stay focused.
UPDATE doris_cluster
SET cluster_name = 'README 演示集群',
    source_type = 'DORIS',
    fe_host = 'localhost',
    fe_port = 3306,
    username = 'opendataworks',
    password = 'opendataworks123',
    is_default = 1,
    status = 'active'
WHERE id = 1;

-- Normalize legacy sample comments that previously appeared as mojibake.
UPDATE data_table
SET table_comment = CASE table_name
    WHEN 'ods_user' THEN '用户原始数据表'
    WHEN 'ods_order' THEN '订单原始数据表'
    WHEN 'dwd_user' THEN '用户明细数据表'
    WHEN 'dwd_order' THEN '订单明细数据表'
    WHEN 'dws_user_daily' THEN '用户日统计表'
    WHEN 'dws_order_daily' THEN '订单日统计表'
    ELSE table_comment
END
WHERE table_name IN (
    'ods_user',
    'ods_order',
    'dwd_user',
    'dwd_order',
    'dws_user_daily',
    'dws_order_daily'
);

-- Rebuild workflow and task related demo data from scratch so list pages stay clean.
DELETE FROM workflow_runtime_sync_record;
DELETE FROM workflow_publish_record;
DELETE FROM workflow_instance_cache;
DELETE FROM workflow_task_relation;
DELETE FROM workflow_version;
DELETE FROM task_execution_log;
DELETE FROM data_lineage;
DELETE FROM table_task_relation;
DELETE FROM dolphin_workflow_config;
DELETE FROM data_workflow;
DELETE FROM data_task;

ALTER TABLE data_task AUTO_INCREMENT = 1;
ALTER TABLE data_workflow AUTO_INCREMENT = 1;
ALTER TABLE workflow_version AUTO_INCREMENT = 1;
ALTER TABLE workflow_task_relation AUTO_INCREMENT = 1;
ALTER TABLE workflow_instance_cache AUTO_INCREMENT = 1;
ALTER TABLE workflow_publish_record AUTO_INCREMENT = 1;
ALTER TABLE task_execution_log AUTO_INCREMENT = 1;

DELETE FROM data_field
WHERE table_id IN (
    SELECT id FROM data_table
    WHERE table_name IN (
        'demo_member_profile',
        'demo_order_event_raw',
        'demo_order_detail',
        'demo_store_sales_daily',
        'demo_order_risk_alert'
    )
);

DELETE FROM data_table
WHERE table_name IN (
    'demo_member_profile',
    'demo_order_event_raw',
    'demo_order_detail',
    'demo_store_sales_daily',
    'demo_order_risk_alert'
);

DROP TABLE IF EXISTS demo_order_risk_alert;
DROP TABLE IF EXISTS demo_store_sales_daily;
DROP TABLE IF EXISTS demo_order_detail;
DROP TABLE IF EXISTS demo_order_event_raw;
DROP TABLE IF EXISTS demo_member_profile;

CREATE TABLE demo_member_profile (
    member_id BIGINT PRIMARY KEY,
    member_level VARCHAR(20) NOT NULL,
    city_name VARCHAR(50) NOT NULL,
    last_active_at DATETIME NOT NULL
) COMMENT='用户画像原始表';

CREATE TABLE demo_order_event_raw (
    order_id BIGINT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    store_id BIGINT NOT NULL,
    order_amount DECIMAL(10, 2) NOT NULL,
    pay_status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL
) COMMENT='订单事件原始表';

CREATE TABLE demo_order_detail (
    order_id BIGINT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    store_id BIGINT NOT NULL,
    city_name VARCHAR(50) NOT NULL,
    member_level VARCHAR(20) NOT NULL,
    order_amount DECIMAL(10, 2) NOT NULL,
    order_date DATE NOT NULL,
    pay_status VARCHAR(20) NOT NULL
) COMMENT='订单明细宽表';

CREATE TABLE demo_store_sales_daily (
    stat_date DATE NOT NULL,
    store_id BIGINT NOT NULL,
    paid_order_cnt INT NOT NULL,
    paid_amount DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (stat_date, store_id)
) COMMENT='门店日销售汇总表';

CREATE TABLE demo_order_risk_alert (
    order_id BIGINT PRIMARY KEY,
    risk_level VARCHAR(20) NOT NULL,
    risk_reason VARCHAR(100) NOT NULL,
    detected_at DATETIME NOT NULL
) COMMENT='订单风险预警表';

INSERT INTO demo_member_profile (member_id, member_level, city_name, last_active_at) VALUES
(1001, 'gold', '上海', '2026-03-10 21:10:00'),
(1002, 'silver', '杭州', '2026-03-10 18:20:00'),
(1003, 'gold', '苏州', '2026-03-10 20:35:00'),
(1004, 'new', '南京', '2026-03-10 16:05:00');

INSERT INTO demo_order_event_raw (order_id, member_id, store_id, order_amount, pay_status, created_at) VALUES
(9001001, 1001, 201, 188.00, 'paid', '2026-03-10 09:12:00'),
(9001002, 1002, 202, 326.50, 'paid', '2026-03-10 10:45:00'),
(9001003, 1003, 201, 88.00, 'paid', '2026-03-10 11:30:00'),
(9001004, 1004, 203, 699.00, 'pending_review', '2026-03-10 14:05:00'),
(9001005, 1001, 201, 59.90, 'paid', '2026-03-10 15:18:00');

INSERT INTO demo_order_detail (order_id, member_id, store_id, city_name, member_level, order_amount, order_date, pay_status) VALUES
(9001001, 1001, 201, '上海', 'gold', 188.00, '2026-03-10', 'paid'),
(9001002, 1002, 202, '杭州', 'silver', 326.50, '2026-03-10', 'paid'),
(9001003, 1003, 201, '苏州', 'gold', 88.00, '2026-03-10', 'paid'),
(9001004, 1004, 203, '南京', 'new', 699.00, '2026-03-10', 'pending_review'),
(9001005, 1001, 201, '上海', 'gold', 59.90, '2026-03-10', 'paid');

INSERT INTO demo_store_sales_daily (stat_date, store_id, paid_order_cnt, paid_amount) VALUES
('2026-03-10', 201, 3, 335.90),
('2026-03-10', 202, 1, 326.50),
('2026-03-10', 203, 0, 0.00);

INSERT INTO demo_order_risk_alert (order_id, risk_level, risk_reason, detected_at) VALUES
(9001004, 'high', '新用户高金额待人工复核', '2026-03-10 14:06:00'),
(9001002, 'medium', '异地支付命中策略', '2026-03-10 10:46:00');

INSERT INTO data_table (
    cluster_id,
    table_name,
    table_type,
    origin_table_name,
    table_comment,
    layer,
    business_domain,
    data_domain,
    custom_identifier,
    statistics_cycle,
    update_type,
    table_model,
    bucket_num,
    replica_num,
    partition_column,
    distribution_column,
    key_columns,
    doris_ddl,
    is_synced,
    sync_time,
    db_name,
    owner,
    status,
    lifecycle_days,
    storage_size,
    row_count,
    doris_update_time,
    doris_create_time
)
VALUES
(
    1,
    'demo_member_profile',
    'BASE TABLE',
    'demo_member_profile',
    '用户画像原始表',
    'ODS',
    'tech',
    'dev',
    'demo_member_profile_tbl',
    '5m',
    'di',
    'DUPLICATE',
    4,
    1,
    'last_active_at',
    'member_id',
    'member_id',
    'CREATE TABLE demo_member_profile (...)',
    1,
    NOW(),
    'opendataworks',
    'readme',
    'active',
    365,
    8192,
    4,
    NOW(),
    NOW()
),
(
    1,
    'demo_order_event_raw',
    'BASE TABLE',
    'demo_order_event_raw',
    '订单事件原始表',
    'ODS',
    'tech',
    'ops',
    'demo_order_event_raw_tbl',
    '5m',
    'di',
    'DUPLICATE',
    8,
    1,
    'created_at',
    'order_id',
    'order_id',
    'CREATE TABLE demo_order_event_raw (...)',
    1,
    NOW(),
    'opendataworks',
    'readme',
    'active',
    365,
    12288,
    5,
    NOW(),
    NOW()
),
(
    1,
    'demo_order_detail',
    'BASE TABLE',
    'demo_order_detail',
    '订单明细宽表',
    'DWD',
    'tech',
    'ops',
    'demo_order_detail_tbl',
    '30m',
    'df',
    'UNIQUE',
    8,
    1,
    'order_date',
    'store_id',
    'order_id',
    'CREATE TABLE demo_order_detail (...)',
    1,
    NOW(),
    'opendataworks',
    'readme',
    'active',
    365,
    16384,
    5,
    NOW(),
    NOW()
),
(
    1,
    'demo_store_sales_daily',
    'BASE TABLE',
    'demo_store_sales_daily',
    '门店日销售汇总表',
    'DWS',
    'tech',
    'ops',
    'demo_store_sales_daily_tbl',
    '1d',
    'di',
    'AGGREGATE',
    4,
    1,
    'stat_date',
    'store_id',
    'stat_date,store_id',
    'CREATE TABLE demo_store_sales_daily (...)',
    1,
    NOW(),
    'opendataworks',
    'readme',
    'active',
    365,
    8192,
    3,
    NOW(),
    NOW()
),
(
    1,
    'demo_order_risk_alert',
    'BASE TABLE',
    'demo_order_risk_alert',
    '订单风险预警表',
    'ADS',
    'tech',
    'ops',
    'demo_order_risk_alert_tbl',
    '30m',
    'mi',
    'UNIQUE',
    4,
    1,
    'detected_at',
    'order_id',
    'order_id',
    'CREATE TABLE demo_order_risk_alert (...)',
    1,
    NOW(),
    'opendataworks',
    'readme',
    'active',
    365,
    4096,
    2,
    NOW(),
    NOW()
);

INSERT INTO data_field (
    table_id,
    field_name,
    field_type,
    field_comment,
    is_nullable,
    is_partition,
    is_primary,
    default_value,
    field_order
)
SELECT dt.id, 'member_id', 'BIGINT', '会员 ID', 0, 0, 1, NULL, 1
FROM data_table dt WHERE dt.table_name = 'demo_member_profile'
UNION ALL
SELECT dt.id, 'member_level', 'VARCHAR(20)', '会员等级', 0, 0, 0, NULL, 2
FROM data_table dt WHERE dt.table_name = 'demo_member_profile'
UNION ALL
SELECT dt.id, 'city_name', 'VARCHAR(50)', '城市', 0, 0, 0, NULL, 3
FROM data_table dt WHERE dt.table_name = 'demo_member_profile'
UNION ALL
SELECT dt.id, 'last_active_at', 'DATETIME', '最近活跃时间', 0, 1, 0, NULL, 4
FROM data_table dt WHERE dt.table_name = 'demo_member_profile'
UNION ALL
SELECT dt.id, 'order_id', 'BIGINT', '订单 ID', 0, 0, 1, NULL, 1
FROM data_table dt WHERE dt.table_name = 'demo_order_event_raw'
UNION ALL
SELECT dt.id, 'member_id', 'BIGINT', '会员 ID', 0, 0, 0, NULL, 2
FROM data_table dt WHERE dt.table_name = 'demo_order_event_raw'
UNION ALL
SELECT dt.id, 'store_id', 'BIGINT', '门店 ID', 0, 0, 0, NULL, 3
FROM data_table dt WHERE dt.table_name = 'demo_order_event_raw'
UNION ALL
SELECT dt.id, 'order_amount', 'DECIMAL(10,2)', '订单金额', 0, 0, 0, '0.00', 4
FROM data_table dt WHERE dt.table_name = 'demo_order_event_raw'
UNION ALL
SELECT dt.id, 'pay_status', 'VARCHAR(20)', '支付状态', 0, 0, 0, NULL, 5
FROM data_table dt WHERE dt.table_name = 'demo_order_event_raw'
UNION ALL
SELECT dt.id, 'created_at', 'DATETIME', '下单时间', 0, 1, 0, NULL, 6
FROM data_table dt WHERE dt.table_name = 'demo_order_event_raw'
UNION ALL
SELECT dt.id, 'order_id', 'BIGINT', '订单 ID', 0, 0, 1, NULL, 1
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'member_id', 'BIGINT', '会员 ID', 0, 0, 0, NULL, 2
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'store_id', 'BIGINT', '门店 ID', 0, 0, 0, NULL, 3
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'city_name', 'VARCHAR(50)', '城市', 0, 0, 0, NULL, 4
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'member_level', 'VARCHAR(20)', '会员等级', 0, 0, 0, NULL, 5
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'order_amount', 'DECIMAL(10,2)', '订单金额', 0, 0, 0, '0.00', 6
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'order_date', 'DATE', '订单日期', 0, 1, 0, NULL, 7
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'pay_status', 'VARCHAR(20)', '支付状态', 0, 0, 0, NULL, 8
FROM data_table dt WHERE dt.table_name = 'demo_order_detail'
UNION ALL
SELECT dt.id, 'stat_date', 'DATE', '统计日期', 0, 1, 1, NULL, 1
FROM data_table dt WHERE dt.table_name = 'demo_store_sales_daily'
UNION ALL
SELECT dt.id, 'store_id', 'BIGINT', '门店 ID', 0, 0, 1, NULL, 2
FROM data_table dt WHERE dt.table_name = 'demo_store_sales_daily'
UNION ALL
SELECT dt.id, 'paid_order_cnt', 'INT', '支付订单数', 0, 0, 0, '0', 3
FROM data_table dt WHERE dt.table_name = 'demo_store_sales_daily'
UNION ALL
SELECT dt.id, 'paid_amount', 'DECIMAL(12,2)', '支付金额', 0, 0, 0, '0.00', 4
FROM data_table dt WHERE dt.table_name = 'demo_store_sales_daily'
UNION ALL
SELECT dt.id, 'order_id', 'BIGINT', '订单 ID', 0, 0, 1, NULL, 1
FROM data_table dt WHERE dt.table_name = 'demo_order_risk_alert'
UNION ALL
SELECT dt.id, 'risk_level', 'VARCHAR(20)', '风险等级', 0, 0, 0, NULL, 2
FROM data_table dt WHERE dt.table_name = 'demo_order_risk_alert'
UNION ALL
SELECT dt.id, 'risk_reason', 'VARCHAR(100)', '风险原因', 0, 0, 0, NULL, 3
FROM data_table dt WHERE dt.table_name = 'demo_order_risk_alert'
UNION ALL
SELECT dt.id, 'detected_at', 'DATETIME', '识别时间', 0, 1, 0, NULL, 4
FROM data_table dt WHERE dt.table_name = 'demo_order_risk_alert';

INSERT INTO data_task (
    task_name,
    task_code,
    task_type,
    engine,
    dolphin_node_type,
    datasource_name,
    datasource_type,
    task_group_name,
    task_sql,
    task_desc,
    schedule_cron,
    priority,
    timeout_seconds,
    retry_times,
    retry_interval,
    owner,
    status,
    source_table,
    target_table,
    created_at,
    updated_at
)
VALUES
(
    'README 演示 - 订单明细加工',
    'readme_demo_build_order_detail',
    'batch',
    'dolphin',
    'SQL',
    'README 演示集群',
    'MYSQL',
    'demo_etl',
    'INSERT INTO demo_order_detail SELECT ... FROM demo_order_event_raw JOIN demo_member_profile ...',
    '将订单事件与会员画像汇总成订单明细宽表。',
    '0 */30 * * * ?',
    6,
    1800,
    1,
    60,
    'readme',
    'published',
    'demo_order_event_raw,demo_member_profile',
    'demo_order_detail',
    '2026-03-10 09:20:00',
    '2026-03-11 09:32:00'
),
(
    'README 演示 - 门店日销售汇总',
    'readme_demo_build_store_sales_daily',
    'batch',
    'dolphin',
    'SQL',
    'README 演示集群',
    'MYSQL',
    'demo_etl',
    'INSERT INTO demo_store_sales_daily SELECT ... FROM demo_order_detail GROUP BY stat_date, store_id',
    '按门店与日期汇总支付订单数和金额。',
    '0 5 2 * * ?',
    5,
    1800,
    1,
    60,
    'readme',
    'running',
    'demo_order_detail',
    'demo_store_sales_daily',
    '2026-03-10 09:40:00',
    '2026-03-11 10:06:00'
),
(
    'README 演示 - 风险订单识别',
    'readme_demo_build_order_risk_alert',
    'stream',
    'dinky',
    'FLINK',
    'README 演示集群',
    'MYSQL',
    'demo_realtime',
    'INSERT INTO demo_order_risk_alert SELECT ... FROM demo_order_detail WHERE pay_status <> ''paid''',
    '从订单明细中识别需要人工复核的风险订单。',
    '0 */10 * * * ?',
    7,
    1200,
    2,
    30,
    'readme',
    'failed',
    'demo_order_detail',
    'demo_order_risk_alert',
    '2026-03-10 10:00:00',
    '2026-03-11 10:12:00'
);

INSERT INTO data_lineage (task_id, upstream_table_id, downstream_table_id, lineage_type)
SELECT t.id, src.id, dst.id, 'input'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_member_profile'
JOIN data_table dst ON dst.table_name = 'demo_order_detail'
WHERE t.task_code = 'readme_demo_build_order_detail'
UNION ALL
SELECT t.id, src.id, dst.id, 'input'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_order_event_raw'
JOIN data_table dst ON dst.table_name = 'demo_order_detail'
WHERE t.task_code = 'readme_demo_build_order_detail'
UNION ALL
SELECT t.id, NULL, dst.id, 'output'
FROM data_task t
JOIN data_table dst ON dst.table_name = 'demo_order_detail'
WHERE t.task_code = 'readme_demo_build_order_detail'
UNION ALL
SELECT t.id, src.id, dst.id, 'input'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_order_detail'
JOIN data_table dst ON dst.table_name = 'demo_store_sales_daily'
WHERE t.task_code = 'readme_demo_build_store_sales_daily'
UNION ALL
SELECT t.id, NULL, dst.id, 'output'
FROM data_task t
JOIN data_table dst ON dst.table_name = 'demo_store_sales_daily'
WHERE t.task_code = 'readme_demo_build_store_sales_daily'
UNION ALL
SELECT t.id, src.id, dst.id, 'input'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_order_detail'
JOIN data_table dst ON dst.table_name = 'demo_order_risk_alert'
WHERE t.task_code = 'readme_demo_build_order_risk_alert'
UNION ALL
SELECT t.id, NULL, dst.id, 'output'
FROM data_task t
JOIN data_table dst ON dst.table_name = 'demo_order_risk_alert'
WHERE t.task_code = 'readme_demo_build_order_risk_alert';

INSERT INTO table_task_relation (table_id, task_id, relation_type)
SELECT src.id, t.id, 'read'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_member_profile'
WHERE t.task_code = 'readme_demo_build_order_detail'
UNION ALL
SELECT src.id, t.id, 'read'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_order_event_raw'
WHERE t.task_code = 'readme_demo_build_order_detail'
UNION ALL
SELECT dst.id, t.id, 'write'
FROM data_task t
JOIN data_table dst ON dst.table_name = 'demo_order_detail'
WHERE t.task_code = 'readme_demo_build_order_detail'
UNION ALL
SELECT src.id, t.id, 'read'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_order_detail'
WHERE t.task_code = 'readme_demo_build_store_sales_daily'
UNION ALL
SELECT dst.id, t.id, 'write'
FROM data_task t
JOIN data_table dst ON dst.table_name = 'demo_store_sales_daily'
WHERE t.task_code = 'readme_demo_build_store_sales_daily'
UNION ALL
SELECT src.id, t.id, 'read'
FROM data_task t
JOIN data_table src ON src.table_name = 'demo_order_detail'
WHERE t.task_code = 'readme_demo_build_order_risk_alert'
UNION ALL
SELECT dst.id, t.id, 'write'
FROM data_task t
JOIN data_table dst ON dst.table_name = 'demo_order_risk_alert'
WHERE t.task_code = 'readme_demo_build_order_risk_alert';

INSERT INTO data_workflow (
    workflow_code,
    project_code,
    workflow_name,
    status,
    publish_status,
    definition_json,
    entry_task_ids,
    exit_task_ids,
    description,
    created_by,
    updated_by,
    created_at,
    updated_at,
    global_params,
    task_group_name,
    dolphin_schedule_id,
    schedule_state,
    schedule_cron,
    schedule_timezone,
    schedule_start_time,
    schedule_end_time,
    schedule_failure_strategy,
    schedule_warning_type,
    schedule_warning_group_id,
    schedule_auto_online,
    schedule_process_instance_priority,
    schedule_worker_group,
    schedule_tenant_code,
    schedule_environment_code,
    sync_source,
    runtime_sync_status,
    runtime_sync_message,
    runtime_sync_at
)
VALUES
(
    NULL,
    20001,
    'README 演示 - 订单主题加工链路',
    'online',
    'published',
    JSON_OBJECT(
        'workflowName', 'README 演示 - 订单主题加工链路',
        'description', '从订单原始数据生成订单明细和门店日汇总的标准加工链路。',
        'nodes', JSON_ARRAY(
            JSON_OBJECT('taskCode', 'readme_demo_build_order_detail', 'name', '订单明细加工'),
            JSON_OBJECT('taskCode', 'readme_demo_build_store_sales_daily', 'name', '门店日销售汇总')
        ),
        'edges', JSON_ARRAY(
            JSON_OBJECT('from', 'readme_demo_build_order_detail', 'to', 'readme_demo_build_store_sales_daily')
        )
    ),
    JSON_ARRAY(),
    JSON_ARRAY(),
    '从订单事件和会员画像生成订单主题宽表，并汇总门店日销售指标。',
    'readme',
    'readme',
    '2026-03-10 09:15:00',
    '2026-03-11 10:08:00',
    JSON_ARRAY(
        JSON_OBJECT('prop', 'biz_date', 'value', '${system.biz.date}', 'direct', 'IN')
    ),
    'demo_etl',
    920001,
    'ONLINE',
    '0 5 2 * * ?',
    'Asia/Shanghai',
    '2026-03-01 00:00:00',
    '2026-12-31 23:59:59',
    'CONTINUE',
    'NONE',
    0,
    1,
    'MEDIUM',
    'default',
    'default',
    -1,
    'manual',
    'success',
    'README 演示数据已同步到本地工作流快照。',
    '2026-03-11 10:08:00'
),
(
    NULL,
    20002,
    'README 演示 - 风险识别链路',
    'offline',
    'published',
    JSON_OBJECT(
        'workflowName', 'README 演示 - 风险识别链路',
        'description', '识别待复核高风险订单并产出预警结果。',
        'nodes', JSON_ARRAY(
            JSON_OBJECT('taskCode', 'readme_demo_build_order_risk_alert', 'name', '风险订单识别')
        ),
        'edges', JSON_ARRAY()
    ),
    JSON_ARRAY(),
    JSON_ARRAY(),
    '基于订单明细识别高风险订单，供风控值班同学复核。',
    'readme',
    'readme',
    '2026-03-10 10:10:00',
    '2026-03-11 10:15:00',
    JSON_ARRAY(
        JSON_OBJECT('prop', 'alert_window_minutes', 'value', '10', 'direct', 'IN')
    ),
    'demo_realtime',
    920002,
    'OFFLINE',
    '0 */10 * * * ?',
    'Asia/Shanghai',
    '2026-03-01 00:00:00',
    '2026-12-31 23:59:59',
    'END',
    'FAILURE',
    0,
    0,
    'HIGH',
    'default',
    'default',
    -1,
    'manual',
    'success',
    'README 演示数据已同步到本地工作流快照。',
    '2026-03-11 10:15:00'
);

SET @workflow_order_chain = (
    SELECT id
    FROM data_workflow
    WHERE workflow_name = 'README 演示 - 订单主题加工链路'
);
SET @workflow_risk_chain = (
    SELECT id
    FROM data_workflow
    WHERE workflow_name = 'README 演示 - 风险识别链路'
);
SET @task_order_detail = (
    SELECT id
    FROM data_task
    WHERE task_code = 'readme_demo_build_order_detail'
);
SET @task_store_sales = (
    SELECT id
    FROM data_task
    WHERE task_code = 'readme_demo_build_store_sales_daily'
);
SET @task_risk_alert = (
    SELECT id
    FROM data_task
    WHERE task_code = 'readme_demo_build_order_risk_alert'
);

INSERT INTO workflow_version (
    workflow_id,
    version_no,
    structure_snapshot,
    change_summary,
    trigger_source,
    created_by,
    created_at,
    snapshot_schema_version,
    rollback_from_version_id
)
VALUES
(
    @workflow_order_chain,
    1,
    JSON_OBJECT(
        'schemaVersion', 3,
        'workflow', JSON_OBJECT(
            'workflowName', 'README 演示 - 订单主题加工链路',
            'status', 'online',
            'scheduleCron', '0 5 2 * * ?'
        ),
        'tasks', JSON_ARRAY(
            JSON_OBJECT('taskId', @task_order_detail, 'taskCode', 'readme_demo_build_order_detail', 'taskName', 'README 演示 - 订单明细加工'),
            JSON_OBJECT('taskId', @task_store_sales, 'taskCode', 'readme_demo_build_store_sales_daily', 'taskName', 'README 演示 - 门店日销售汇总')
        ),
        'edges', JSON_ARRAY(
            JSON_OBJECT('fromTaskId', @task_order_detail, 'toTaskId', @task_store_sales)
        )
    ),
    '初始化订单主题加工工作流。',
    'manual',
    'readme',
    '2026-03-10 09:18:00',
    3,
    NULL
),
(
    @workflow_risk_chain,
    1,
    JSON_OBJECT(
        'schemaVersion', 3,
        'workflow', JSON_OBJECT(
            'workflowName', 'README 演示 - 风险识别链路',
            'status', 'offline',
            'scheduleCron', '0 */10 * * * ?'
        ),
        'tasks', JSON_ARRAY(
            JSON_OBJECT('taskId', @task_risk_alert, 'taskCode', 'readme_demo_build_order_risk_alert', 'taskName', 'README 演示 - 风险订单识别')
        ),
        'edges', JSON_ARRAY()
    ),
    '初始化风险识别工作流。',
    'manual',
    'readme',
    '2026-03-10 10:12:00',
    3,
    NULL
);

SET @version_order_chain = (
    SELECT id
    FROM workflow_version
    WHERE workflow_id = @workflow_order_chain AND version_no = 1
);
SET @version_risk_chain = (
    SELECT id
    FROM workflow_version
    WHERE workflow_id = @workflow_risk_chain AND version_no = 1
);

UPDATE data_workflow
SET current_version_id = CASE id
        WHEN @workflow_order_chain THEN @version_order_chain
        WHEN @workflow_risk_chain THEN @version_risk_chain
        ELSE current_version_id
    END,
    last_published_version_id = CASE id
        WHEN @workflow_order_chain THEN @version_order_chain
        WHEN @workflow_risk_chain THEN @version_risk_chain
        ELSE last_published_version_id
    END,
    entry_task_ids = CASE id
        WHEN @workflow_order_chain THEN JSON_ARRAY(@task_order_detail)
        WHEN @workflow_risk_chain THEN JSON_ARRAY(@task_risk_alert)
        ELSE entry_task_ids
    END,
    exit_task_ids = CASE id
        WHEN @workflow_order_chain THEN JSON_ARRAY(@task_store_sales)
        WHEN @workflow_risk_chain THEN JSON_ARRAY(@task_risk_alert)
        ELSE exit_task_ids
    END
WHERE id IN (@workflow_order_chain, @workflow_risk_chain);

INSERT INTO workflow_task_relation (
    workflow_id,
    task_id,
    node_attrs,
    is_entry,
    is_exit,
    version_id,
    upstream_task_count,
    downstream_task_count,
    created_at,
    updated_at
)
VALUES
(
    @workflow_order_chain,
    @task_order_detail,
    JSON_OBJECT('x', 220, 'y', 120, 'workerGroup', 'default', 'priority', 'MEDIUM'),
    1,
    0,
    @version_order_chain,
    0,
    1,
    '2026-03-10 09:19:00',
    '2026-03-11 09:32:00'
),
(
    @workflow_order_chain,
    @task_store_sales,
    JSON_OBJECT('x', 500, 'y', 120, 'workerGroup', 'default', 'priority', 'MEDIUM'),
    0,
    1,
    @version_order_chain,
    1,
    0,
    '2026-03-10 09:21:00',
    '2026-03-11 10:06:00'
),
(
    @workflow_risk_chain,
    @task_risk_alert,
    JSON_OBJECT('x', 320, 'y', 120, 'workerGroup', 'default', 'priority', 'HIGH'),
    1,
    1,
    @version_risk_chain,
    0,
    0,
    '2026-03-10 10:14:00',
    '2026-03-11 10:12:00'
);

INSERT INTO workflow_instance_cache (
    workflow_id,
    instance_id,
    state,
    start_time,
    end_time,
    trigger_type,
    duration_ms,
    extra,
    created_at
)
VALUES
(
    @workflow_order_chain,
    810001,
    'SUCCESS',
    '2026-03-11 09:30:00',
    '2026-03-11 09:36:00',
    'schedule',
    360000,
    JSON_OBJECT('bizDate', '2026-03-11', 'owner', 'readme'),
    '2026-03-11 09:36:00'
),
(
    @workflow_order_chain,
    809998,
    'SUCCESS',
    '2026-03-10 09:30:00',
    '2026-03-10 09:37:00',
    'schedule',
    420000,
    JSON_OBJECT('bizDate', '2026-03-10', 'owner', 'readme'),
    '2026-03-10 09:37:00'
),
(
    @workflow_risk_chain,
    820014,
    'FAILED',
    '2026-03-11 10:10:00',
    '2026-03-11 10:12:00',
    'schedule',
    120000,
    JSON_OBJECT('bizDate', '2026-03-11', 'owner', 'risk_oncall'),
    '2026-03-11 10:12:00'
);

INSERT INTO workflow_publish_record (
    workflow_id,
    version_id,
    target_engine,
    operation,
    status,
    engine_workflow_code,
    log,
    operator,
    created_at
)
VALUES
(
    @workflow_order_chain,
    @version_order_chain,
    'dolphin',
    'deploy',
    'success',
    NULL,
    JSON_OBJECT('message', '已生成本地演示工作流定义', 'taskCount', 2),
    'readme',
    '2026-03-10 09:25:00'
),
(
    @workflow_order_chain,
    @version_order_chain,
    'dolphin',
    'online',
    'success',
    NULL,
    JSON_OBJECT('message', '调度已上线，等待次日 02:05 触发', 'scheduleState', 'ONLINE'),
    'readme',
    '2026-03-10 09:26:00'
),
(
    @workflow_risk_chain,
    @version_risk_chain,
    'dolphin',
    'deploy',
    'success',
    NULL,
    JSON_OBJECT('message', '已生成本地演示工作流定义', 'taskCount', 1),
    'readme',
    '2026-03-10 10:16:00'
),
(
    @workflow_risk_chain,
    @version_risk_chain,
    'dolphin',
    'offline',
    'success',
    NULL,
    JSON_OBJECT('message', '因风控策略调整，演示调度保持下线', 'scheduleState', 'OFFLINE'),
    'readme',
    '2026-03-11 10:13:00'
);

INSERT INTO task_execution_log (
    task_id,
    execution_id,
    status,
    start_time,
    end_time,
    duration_seconds,
    rows_output,
    error_message,
    log_url,
    trigger_type,
    created_at,
    updated_at
)
VALUES
(
    @task_order_detail,
    'local-demo-810001-01',
    'success',
    '2026-03-11 09:30:00',
    '2026-03-11 09:32:40',
    160,
    5,
    NULL,
    NULL,
    'schedule',
    '2026-03-11 09:32:40',
    '2026-03-11 09:32:40'
),
(
    @task_order_detail,
    'local-demo-809998-01',
    'success',
    '2026-03-10 09:30:00',
    '2026-03-10 09:33:05',
    185,
    5,
    NULL,
    NULL,
    'schedule',
    '2026-03-10 09:33:05',
    '2026-03-10 09:33:05'
),
(
    @task_store_sales,
    'local-demo-810001-02',
    'running',
    '2026-03-11 10:05:00',
    NULL,
    NULL,
    3,
    NULL,
    NULL,
    'manual',
    '2026-03-11 10:05:00',
    '2026-03-11 10:06:00'
),
(
    @task_store_sales,
    'local-demo-809998-02',
    'success',
    '2026-03-10 09:35:00',
    '2026-03-10 09:36:45',
    105,
    3,
    NULL,
    NULL,
    'schedule',
    '2026-03-10 09:36:45',
    '2026-03-10 09:36:45'
),
(
    @task_risk_alert,
    'local-demo-820014-01',
    'failed',
    '2026-03-11 10:10:00',
    '2026-03-11 10:12:10',
    130,
    2,
    '命中风控规则配置校验，已阻断自动发送。',
    NULL,
    'schedule',
    '2026-03-11 10:12:10',
    '2026-03-11 10:12:10'
),
(
    @task_risk_alert,
    'local-demo-820008-01',
    'success',
    '2026-03-10 10:00:00',
    '2026-03-10 10:01:35',
    95,
    2,
    NULL,
    NULL,
    'api',
    '2026-03-10 10:01:35',
    '2026-03-10 10:01:35'
);
