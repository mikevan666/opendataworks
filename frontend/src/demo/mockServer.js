const DEMO_CLUSTER_ID = 1
const DEMO_DATABASE = 'opendataworks'

const baseTableFields = {
  1232: [
    { id: 21001, fieldName: 'member_id', fieldType: 'BIGINT', fieldComment: '会员 ID', isNullable: 0, isPrimary: 1, fieldOrder: 1, defaultValue: '' },
    { id: 21002, fieldName: 'member_name', fieldType: 'VARCHAR(50)', fieldComment: '会员姓名', isNullable: 1, isPrimary: 0, fieldOrder: 2, defaultValue: '' },
    { id: 21003, fieldName: 'member_level', fieldType: 'VARCHAR(20)', fieldComment: '会员等级', isNullable: 1, isPrimary: 0, fieldOrder: 3, defaultValue: '' },
    { id: 21004, fieldName: 'city_name', fieldType: 'VARCHAR(50)', fieldComment: '城市', isNullable: 1, isPrimary: 0, fieldOrder: 4, defaultValue: '' },
    { id: 21005, fieldName: 'last_active_at', fieldType: 'DATETIME', fieldComment: '最近活跃时间', isNullable: 1, isPrimary: 0, fieldOrder: 5, defaultValue: '' }
  ],
  1233: [
    { id: 22001, fieldName: 'order_id', fieldType: 'BIGINT', fieldComment: '订单 ID', isNullable: 0, isPrimary: 1, fieldOrder: 1, defaultValue: '' },
    { id: 22002, fieldName: 'member_id', fieldType: 'BIGINT', fieldComment: '会员 ID', isNullable: 0, isPrimary: 0, fieldOrder: 2, defaultValue: '' },
    { id: 22003, fieldName: 'store_id', fieldType: 'BIGINT', fieldComment: '门店 ID', isNullable: 0, isPrimary: 0, fieldOrder: 3, defaultValue: '' },
    { id: 22004, fieldName: 'order_amount', fieldType: 'DECIMAL(10,2)', fieldComment: '订单金额', isNullable: 1, isPrimary: 0, fieldOrder: 4, defaultValue: '' },
    { id: 22005, fieldName: 'created_at', fieldType: 'DATETIME', fieldComment: '事件时间', isNullable: 1, isPrimary: 0, fieldOrder: 5, defaultValue: '' },
    { id: 22006, fieldName: 'pay_status', fieldType: 'VARCHAR(20)', fieldComment: '支付状态', isNullable: 1, isPrimary: 0, fieldOrder: 6, defaultValue: '' }
  ],
  1234: [
    { id: 23001, fieldName: 'order_id', fieldType: 'BIGINT', fieldComment: '订单 ID', isNullable: 0, isPrimary: 1, fieldOrder: 1, defaultValue: '' },
    { id: 23002, fieldName: 'member_id', fieldType: 'BIGINT', fieldComment: '会员 ID', isNullable: 0, isPrimary: 0, fieldOrder: 2, defaultValue: '' },
    { id: 23003, fieldName: 'store_id', fieldType: 'BIGINT', fieldComment: '门店 ID', isNullable: 0, isPrimary: 0, fieldOrder: 3, defaultValue: '' },
    { id: 23004, fieldName: 'city_name', fieldType: 'VARCHAR(50)', fieldComment: '城市', isNullable: 1, isPrimary: 0, fieldOrder: 4, defaultValue: '' },
    { id: 23005, fieldName: 'member_level', fieldType: 'VARCHAR(20)', fieldComment: '会员等级', isNullable: 1, isPrimary: 0, fieldOrder: 5, defaultValue: '' },
    { id: 23006, fieldName: 'order_amount', fieldType: 'DECIMAL(10,2)', fieldComment: '订单金额', isNullable: 1, isPrimary: 0, fieldOrder: 6, defaultValue: '' },
    { id: 23007, fieldName: 'order_date', fieldType: 'DATE', fieldComment: '订单日期', isNullable: 1, isPrimary: 0, fieldOrder: 7, defaultValue: '' },
    { id: 23008, fieldName: 'pay_status', fieldType: 'VARCHAR(20)', fieldComment: '支付状态', isNullable: 1, isPrimary: 0, fieldOrder: 8, defaultValue: '' }
  ],
  1235: [
    { id: 24001, fieldName: 'stat_date', fieldType: 'DATE', fieldComment: '统计日期', isNullable: 0, isPrimary: 1, fieldOrder: 1, defaultValue: '' },
    { id: 24002, fieldName: 'store_id', fieldType: 'BIGINT', fieldComment: '门店 ID', isNullable: 0, isPrimary: 1, fieldOrder: 2, defaultValue: '' },
    { id: 24003, fieldName: 'paid_order_cnt', fieldType: 'BIGINT', fieldComment: '支付订单数', isNullable: 1, isPrimary: 0, fieldOrder: 3, defaultValue: '' },
    { id: 24004, fieldName: 'paid_order_amount', fieldType: 'DECIMAL(12,2)', fieldComment: '支付订单金额', isNullable: 1, isPrimary: 0, fieldOrder: 4, defaultValue: '' }
  ],
  1236: [
    { id: 25001, fieldName: 'order_id', fieldType: 'BIGINT', fieldComment: '订单 ID', isNullable: 0, isPrimary: 1, fieldOrder: 1, defaultValue: '' },
    { id: 25002, fieldName: 'risk_level', fieldType: 'VARCHAR(20)', fieldComment: '风险等级', isNullable: 1, isPrimary: 0, fieldOrder: 2, defaultValue: '' },
    { id: 25003, fieldName: 'risk_reason', fieldType: 'VARCHAR(100)', fieldComment: '风险原因', isNullable: 1, isPrimary: 0, fieldOrder: 3, defaultValue: '' },
    { id: 25004, fieldName: 'detected_at', fieldType: 'DATETIME', fieldComment: '识别时间', isNullable: 1, isPrimary: 0, fieldOrder: 4, defaultValue: '' }
  ]
}

const baseTables = [
  {
    id: 1232,
    clusterId: DEMO_CLUSTER_ID,
    tableName: 'demo_member_profile',
    tableType: 'BASE TABLE',
    originTableName: 'demo_member_profile',
    tableComment: '用户画像原始表',
    layer: 'ODS',
    businessDomain: 'tech',
    dataDomain: 'dev',
    customIdentifier: 'demo_member_profile_tbl',
    statisticsCycle: '5m',
    updateType: 'di',
    tableModel: 'DUPLICATE',
    bucketNum: 4,
    replicaNum: 1,
    dbName: DEMO_DATABASE,
    owner: 'readme',
    status: 'active',
    lifecycleDays: 365,
    partitionColumn: 'last_active_at',
    distributionColumn: 'member_id',
    keyColumns: 'member_id',
    dorisDdl: `CREATE TABLE \`demo_member_profile\` (
  \`member_id\` BIGINT NOT NULL,
  \`member_name\` VARCHAR(50),
  \`member_level\` VARCHAR(20),
  \`city_name\` VARCHAR(50),
  \`last_active_at\` DATETIME
) ENGINE=OLAP
DUPLICATE KEY(\`member_id\`)
COMMENT '用户画像原始表';`,
    isSynced: 1,
    syncTime: '2026-03-11T04:51:14',
    storageSize: 8192,
    dorisCreateTime: '2026-03-11T04:51:14',
    rowCount: 4,
    dorisUpdateTime: '2026-03-11T04:51:14',
    createdAt: '2026-03-11T04:51:14',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0
  },
  {
    id: 1233,
    clusterId: DEMO_CLUSTER_ID,
    tableName: 'demo_order_event_raw',
    tableType: 'BASE TABLE',
    originTableName: 'demo_order_event_raw',
    tableComment: '订单事件原始表',
    layer: 'ODS',
    businessDomain: 'tech',
    dataDomain: 'ops',
    customIdentifier: 'demo_order_event_raw_tbl',
    statisticsCycle: '5m',
    updateType: 'di',
    tableModel: 'DUPLICATE',
    bucketNum: 8,
    replicaNum: 1,
    dbName: DEMO_DATABASE,
    owner: 'readme',
    status: 'active',
    lifecycleDays: 365,
    partitionColumn: 'created_at',
    distributionColumn: 'order_id',
    keyColumns: 'order_id',
    dorisDdl: `CREATE TABLE \`demo_order_event_raw\` (
  \`order_id\` BIGINT NOT NULL,
  \`member_id\` BIGINT NOT NULL,
  \`store_id\` BIGINT NOT NULL,
  \`order_amount\` DECIMAL(10,2),
  \`created_at\` DATETIME,
  \`pay_status\` VARCHAR(20)
) ENGINE=OLAP
DUPLICATE KEY(\`order_id\`)
COMMENT '订单事件原始表';`,
    isSynced: 1,
    syncTime: '2026-03-11T04:51:14',
    storageSize: 12288,
    dorisCreateTime: '2026-03-11T04:51:14',
    rowCount: 5,
    dorisUpdateTime: '2026-03-11T04:51:14',
    createdAt: '2026-03-11T04:51:14',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0
  },
  {
    id: 1234,
    clusterId: DEMO_CLUSTER_ID,
    tableName: 'demo_order_detail',
    tableType: 'BASE TABLE',
    originTableName: 'demo_order_detail',
    tableComment: '订单明细宽表',
    layer: 'DWD',
    businessDomain: 'tech',
    dataDomain: 'ops',
    customIdentifier: 'demo_order_detail_tbl',
    statisticsCycle: '30m',
    updateType: 'df',
    tableModel: 'UNIQUE',
    bucketNum: 8,
    replicaNum: 1,
    dbName: DEMO_DATABASE,
    owner: 'readme',
    status: 'active',
    lifecycleDays: 365,
    partitionColumn: 'order_date',
    distributionColumn: 'store_id',
    keyColumns: 'order_id',
    dorisDdl: `CREATE TABLE \`demo_order_detail\` (
  \`order_id\` BIGINT NOT NULL,
  \`member_id\` BIGINT NOT NULL,
  \`store_id\` BIGINT NOT NULL,
  \`city_name\` VARCHAR(50),
  \`member_level\` VARCHAR(20),
  \`order_amount\` DECIMAL(10,2),
  \`order_date\` DATE,
  \`pay_status\` VARCHAR(20)
) ENGINE=OLAP
UNIQUE KEY(\`order_id\`)
COMMENT '订单明细宽表';`,
    isSynced: 1,
    syncTime: '2026-03-11T04:51:14',
    storageSize: 16384,
    dorisCreateTime: '2026-03-11T04:51:14',
    rowCount: 5,
    dorisUpdateTime: '2026-03-11T04:51:14',
    createdAt: '2026-03-11T04:51:14',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0
  },
  {
    id: 1235,
    clusterId: DEMO_CLUSTER_ID,
    tableName: 'demo_store_sales_daily',
    tableType: 'BASE TABLE',
    originTableName: 'demo_store_sales_daily',
    tableComment: '门店日销售汇总表',
    layer: 'DWS',
    businessDomain: 'tech',
    dataDomain: 'ops',
    customIdentifier: 'demo_store_sales_daily_tbl',
    statisticsCycle: '1d',
    updateType: 'di',
    tableModel: 'AGGREGATE',
    bucketNum: 4,
    replicaNum: 1,
    dbName: DEMO_DATABASE,
    owner: 'readme',
    status: 'active',
    lifecycleDays: 365,
    partitionColumn: 'stat_date',
    distributionColumn: 'store_id',
    keyColumns: 'stat_date,store_id',
    dorisDdl: `CREATE TABLE \`demo_store_sales_daily\` (
  \`stat_date\` DATE NOT NULL,
  \`store_id\` BIGINT NOT NULL,
  \`paid_order_cnt\` BIGINT SUM,
  \`paid_order_amount\` DECIMAL(12,2) SUM
) ENGINE=OLAP
AGGREGATE KEY(\`stat_date\`, \`store_id\`)
COMMENT '门店日销售汇总表';`,
    isSynced: 1,
    syncTime: '2026-03-11T04:51:14',
    storageSize: 8192,
    dorisCreateTime: '2026-03-11T04:51:14',
    rowCount: 3,
    dorisUpdateTime: '2026-03-11T04:51:14',
    createdAt: '2026-03-11T04:51:14',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0
  },
  {
    id: 1236,
    clusterId: DEMO_CLUSTER_ID,
    tableName: 'demo_order_risk_alert',
    tableType: 'BASE TABLE',
    originTableName: 'demo_order_risk_alert',
    tableComment: '订单风险预警表',
    layer: 'ADS',
    businessDomain: 'tech',
    dataDomain: 'ops',
    customIdentifier: 'demo_order_risk_alert_tbl',
    statisticsCycle: '30m',
    updateType: 'mi',
    tableModel: 'UNIQUE',
    bucketNum: 4,
    replicaNum: 1,
    dbName: DEMO_DATABASE,
    owner: 'readme',
    status: 'active',
    lifecycleDays: 365,
    partitionColumn: 'detected_at',
    distributionColumn: 'order_id',
    keyColumns: 'order_id',
    dorisDdl: `CREATE TABLE \`demo_order_risk_alert\` (
  \`order_id\` BIGINT NOT NULL,
  \`risk_level\` VARCHAR(20),
  \`risk_reason\` VARCHAR(100),
  \`detected_at\` DATETIME
) ENGINE=OLAP
UNIQUE KEY(\`order_id\`)
COMMENT '订单风险预警表';`,
    isSynced: 1,
    syncTime: '2026-03-11T04:51:14',
    storageSize: 4096,
    dorisCreateTime: '2026-03-11T04:51:14',
    rowCount: 2,
    dorisUpdateTime: '2026-03-11T04:51:14',
    createdAt: '2026-03-11T04:51:14',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0
  }
]

const tableRows = {
  demo_member_profile: [
    { member_id: 1001, member_name: '林青', member_level: 'gold', city_name: '上海', last_active_at: '2026-03-10 19:12:00' },
    { member_id: 1002, member_name: '周舟', member_level: 'silver', city_name: '杭州', last_active_at: '2026-03-10 18:40:00' },
    { member_id: 1003, member_name: '沈野', member_level: 'gold', city_name: '苏州', last_active_at: '2026-03-10 18:05:00' },
    { member_id: 1004, member_name: '魏宁', member_level: 'new', city_name: '南京', last_active_at: '2026-03-10 17:20:00' }
  ],
  demo_order_event_raw: [
    { order_id: 9001001, member_id: 1001, store_id: 201, order_amount: 188.0, created_at: '2026-03-10 09:30:12', pay_status: 'paid' },
    { order_id: 9001002, member_id: 1002, store_id: 202, order_amount: 326.5, created_at: '2026-03-10 09:40:56', pay_status: 'paid' },
    { order_id: 9001003, member_id: 1003, store_id: 201, order_amount: 88.0, created_at: '2026-03-10 10:11:02', pay_status: 'paid' },
    { order_id: 9001004, member_id: 1004, store_id: 203, order_amount: 699.0, created_at: '2026-03-10 10:54:40', pay_status: 'pending_review' },
    { order_id: 9001005, member_id: 1001, store_id: 201, order_amount: 59.9, created_at: '2026-03-10 11:20:28', pay_status: 'paid' }
  ],
  demo_order_detail: [
    { order_id: 9001001, member_id: 1001, store_id: 201, city_name: '上海', member_level: 'gold', order_amount: 188.0, order_date: '2026-03-10', pay_status: 'paid' },
    { order_id: 9001002, member_id: 1002, store_id: 202, city_name: '杭州', member_level: 'silver', order_amount: 326.5, order_date: '2026-03-10', pay_status: 'paid' },
    { order_id: 9001003, member_id: 1003, store_id: 201, city_name: '苏州', member_level: 'gold', order_amount: 88.0, order_date: '2026-03-10', pay_status: 'paid' },
    { order_id: 9001004, member_id: 1004, store_id: 203, city_name: '南京', member_level: 'new', order_amount: 699.0, order_date: '2026-03-10', pay_status: 'pending_review' },
    { order_id: 9001005, member_id: 1001, store_id: 201, city_name: '上海', member_level: 'gold', order_amount: 59.9, order_date: '2026-03-10', pay_status: 'paid' }
  ],
  demo_store_sales_daily: [
    { stat_date: '2026-03-10', store_id: 201, paid_order_cnt: 3, paid_order_amount: 335.9 },
    { stat_date: '2026-03-10', store_id: 202, paid_order_cnt: 1, paid_order_amount: 326.5 },
    { stat_date: '2026-03-10', store_id: 203, paid_order_cnt: 0, paid_order_amount: 0.0 }
  ],
  demo_order_risk_alert: [
    { order_id: 9001004, risk_level: 'high', risk_reason: '待人工复核', detected_at: '2026-03-11 10:10:05' },
    { order_id: 9001010, risk_level: 'medium', risk_reason: '地址异常', detected_at: '2026-03-11 09:58:14' }
  ]
}

const baseWorkflows = [
  {
    id: 2,
    workflowCode: null,
    projectCode: 20002,
    workflowName: 'README 演示 - 风险识别链路',
    status: 'offline',
    publishStatus: 'published',
    currentVersionId: 2,
    lastPublishedVersionId: 2,
    description: '基于订单明细识别高风险订单，供风控值班同学复核。',
    createdBy: 'readme',
    updatedBy: 'readme',
    taskGroupName: 'demo_realtime',
    dolphinScheduleId: 920002,
    scheduleState: 'OFFLINE',
    scheduleCron: '0 */10 * * * ?',
    scheduleTimezone: 'Asia/Shanghai',
    scheduleStartTime: '2026-03-01T00:00:00',
    scheduleEndTime: '2026-12-31T23:59:59',
    syncSource: 'manual',
    runtimeSyncStatus: 'success',
    runtimeSyncMessage: '演示数据已同步到本地工作流快照。',
    runtimeSyncAt: '2026-03-11T10:15:00',
    createdAt: '2026-03-10T10:10:00',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0,
    latestInstanceId: 820014,
    latestInstanceState: 'FAILED',
    latestInstanceStartTime: '2026-03-11T10:10:00',
    latestInstanceEndTime: '2026-03-11T10:12:00',
    currentVersionNo: 1
  },
  {
    id: 1,
    workflowCode: null,
    projectCode: 20001,
    workflowName: 'README 演示 - 订单主题加工链路',
    status: 'online',
    publishStatus: 'published',
    currentVersionId: 1,
    lastPublishedVersionId: 1,
    description: '从订单事件和会员画像生成订单主题宽表，并汇总门店日销售指标。',
    createdBy: 'readme',
    updatedBy: 'readme',
    taskGroupName: 'demo_etl',
    dolphinScheduleId: 920001,
    scheduleState: 'ONLINE',
    scheduleCron: '0 5 2 * * ?',
    scheduleTimezone: 'Asia/Shanghai',
    scheduleStartTime: '2026-03-01T00:00:00',
    scheduleEndTime: '2026-12-31T23:59:59',
    syncSource: 'manual',
    runtimeSyncStatus: 'success',
    runtimeSyncMessage: '演示数据已同步到本地工作流快照。',
    runtimeSyncAt: '2026-03-11T10:08:00',
    createdAt: '2026-03-10T09:15:00',
    updatedAt: '2026-03-11T04:51:14',
    deleted: 0,
    latestInstanceId: 810001,
    latestInstanceState: 'SUCCESS',
    latestInstanceStartTime: '2026-03-11T09:30:00',
    latestInstanceEndTime: '2026-03-11T09:36:00',
    currentVersionNo: 1
  }
]

const baseTasks = [
  {
    id: 3,
    taskName: 'README 演示 - 风险订单识别',
    taskCode: 'readme_demo_build_order_risk_alert',
    taskType: 'stream',
    engine: 'dinky',
    dolphinNodeType: 'FLINK',
    datasourceName: 'README 演示集群',
    datasourceType: 'MYSQL',
    taskGroupName: 'demo_realtime',
    sourceTable: 'demo_order_detail',
    targetTable: 'demo_order_risk_alert',
    taskSql: 'INSERT INTO demo_order_risk_alert SELECT ... FROM demo_order_detail WHERE pay_status <> \'paid\'',
    taskDesc: '从订单明细中识别需要人工复核的风险订单。',
    scheduleCron: '0 */10 * * * ?',
    priority: 7,
    timeoutSeconds: 1200,
    retryTimes: 2,
    retryInterval: 30,
    owner: 'readme',
    status: 'failed',
    dolphinTaskVersion: 1,
    createdAt: '2026-03-10T10:00:00',
    updatedAt: '2026-03-11T10:12:00',
    deleted: 0,
    workflowId: 2,
    workflowName: 'README 演示 - 风险识别链路',
    upstreamTaskCount: 0,
    downstreamTaskCount: 0,
    executionStatus: {
      taskId: 3,
      executionId: 'local-demo-820014-01',
      status: 'failed',
      startTime: '2026-03-11T10:10:00',
      endTime: '2026-03-11T10:12:10',
      durationSeconds: 130,
      errorMessage: '命中风控规则配置校验，已阻断自动发送。',
      logUrl: null,
      triggerType: 'schedule',
      dolphinWorkflowCode: null,
      dolphinTaskCode: null,
      dolphinWorkflowUrl: null,
      dolphinTaskUrl: null,
      dolphinProjectName: 'README 演示 - 风险识别链路'
    }
  },
  {
    id: 2,
    taskName: 'README 演示 - 门店日销售汇总',
    taskCode: 'readme_demo_build_store_sales_daily',
    taskType: 'batch',
    engine: 'dolphin',
    dolphinNodeType: 'SQL',
    datasourceName: 'README 演示集群',
    datasourceType: 'MYSQL',
    taskGroupName: 'demo_etl',
    sourceTable: 'demo_order_detail',
    targetTable: 'demo_store_sales_daily',
    taskSql: 'INSERT INTO demo_store_sales_daily SELECT ... FROM demo_order_detail GROUP BY stat_date, store_id',
    taskDesc: '按门店与日期汇总支付订单数和金额。',
    scheduleCron: '0 5 2 * * ?',
    priority: 5,
    timeoutSeconds: 1800,
    retryTimes: 1,
    retryInterval: 60,
    owner: 'readme',
    status: 'running',
    dolphinTaskVersion: 1,
    createdAt: '2026-03-10T09:40:00',
    updatedAt: '2026-03-11T10:06:00',
    deleted: 0,
    workflowId: 1,
    workflowName: 'README 演示 - 订单主题加工链路',
    upstreamTaskCount: 1,
    downstreamTaskCount: 0,
    executionStatus: {
      taskId: 2,
      executionId: 'local-demo-810001-02',
      status: 'running',
      startTime: '2026-03-11T10:05:00',
      endTime: null,
      durationSeconds: null,
      errorMessage: null,
      logUrl: null,
      triggerType: 'manual',
      dolphinWorkflowCode: null,
      dolphinTaskCode: null,
      dolphinWorkflowUrl: null,
      dolphinTaskUrl: null,
      dolphinProjectName: 'README 演示 - 订单主题加工链路'
    }
  },
  {
    id: 1,
    taskName: 'README 演示 - 订单明细加工',
    taskCode: 'readme_demo_build_order_detail',
    taskType: 'batch',
    engine: 'dolphin',
    dolphinNodeType: 'SQL',
    datasourceName: 'README 演示集群',
    datasourceType: 'MYSQL',
    taskGroupName: 'demo_etl',
    sourceTable: 'demo_order_event_raw,demo_member_profile',
    targetTable: 'demo_order_detail',
    taskSql: 'INSERT INTO demo_order_detail SELECT ... FROM demo_order_event_raw JOIN demo_member_profile ...',
    taskDesc: '将订单事件与会员画像汇总成订单明细宽表。',
    scheduleCron: '0 */30 * * * ?',
    priority: 6,
    timeoutSeconds: 1800,
    retryTimes: 1,
    retryInterval: 60,
    owner: 'readme',
    status: 'published',
    dolphinTaskVersion: 1,
    createdAt: '2026-03-10T09:20:00',
    updatedAt: '2026-03-11T09:32:00',
    deleted: 0,
    workflowId: 1,
    workflowName: 'README 演示 - 订单主题加工链路',
    upstreamTaskCount: 0,
    downstreamTaskCount: 1,
    executionStatus: {
      taskId: 1,
      executionId: 'local-demo-810001-01',
      status: 'success',
      startTime: '2026-03-11T09:30:00',
      endTime: '2026-03-11T09:32:40',
      durationSeconds: 160,
      errorMessage: null,
      logUrl: null,
      triggerType: 'schedule',
      dolphinWorkflowCode: null,
      dolphinTaskCode: null,
      dolphinWorkflowUrl: null,
      dolphinTaskUrl: null,
      dolphinProjectName: 'README 演示 - 订单主题加工链路'
    }
  }
]

const baseExecutions = [
  {
    id: 6,
    taskId: 1,
    executionId: 'local-demo-810001-03',
    status: 'success',
    startTime: '2026-03-11T07:30:00',
    endTime: '2026-03-11T07:32:02',
    durationSeconds: 122,
    rowsOutput: 5,
    errorMessage: null,
    logUrl: null,
    triggerType: 'schedule',
    createdAt: '2026-03-11T07:32:02',
    updatedAt: '2026-03-11T07:32:02',
    workflowCode: null,
    workflowName: 'README 演示 - 订单主题加工链路',
    taskCode: 'readme_demo_build_order_detail',
    workflowInstanceUrl: null,
    taskDefinitionUrl: null,
    dolphinInstanceId: null,
    dolphinState: null,
    dolphinStartTime: null,
    dolphinEndTime: null,
    dolphinDuration: null,
    runTimes: 1,
    host: 'demo-worker-01',
    commandType: 'SCHEDULER'
  },
  {
    id: 5,
    taskId: 3,
    executionId: 'local-demo-820014-01',
    status: 'failed',
    startTime: '2026-03-11T10:10:00',
    endTime: '2026-03-11T10:12:10',
    durationSeconds: 130,
    rowsOutput: 2,
    errorMessage: '命中风控规则配置校验，已阻断自动发送。',
    logUrl: null,
    triggerType: 'schedule',
    createdAt: '2026-03-11T10:12:10',
    updatedAt: '2026-03-11T10:12:10',
    workflowCode: null,
    workflowName: 'README 演示 - 风险识别链路',
    taskCode: 'readme_demo_build_order_risk_alert',
    workflowInstanceUrl: null,
    taskDefinitionUrl: null,
    dolphinInstanceId: null,
    dolphinState: null,
    dolphinStartTime: null,
    dolphinEndTime: null,
    dolphinDuration: null,
    runTimes: 1,
    host: 'demo-worker-02',
    commandType: 'SCHEDULER'
  },
  {
    id: 4,
    taskId: 3,
    executionId: 'local-demo-820014-00',
    status: 'success',
    startTime: '2026-03-11T09:50:00',
    endTime: '2026-03-11T09:51:28',
    durationSeconds: 88,
    rowsOutput: 1,
    errorMessage: null,
    logUrl: null,
    triggerType: 'schedule',
    createdAt: '2026-03-11T09:51:28',
    updatedAt: '2026-03-11T09:51:28',
    workflowCode: null,
    workflowName: 'README 演示 - 风险识别链路',
    taskCode: 'readme_demo_build_order_risk_alert',
    workflowInstanceUrl: null,
    taskDefinitionUrl: null,
    dolphinInstanceId: null,
    dolphinState: null,
    dolphinStartTime: null,
    dolphinEndTime: null,
    dolphinDuration: null,
    runTimes: 1,
    host: 'demo-worker-02',
    commandType: 'SCHEDULER'
  },
  {
    id: 3,
    taskId: 2,
    executionId: 'local-demo-810001-02',
    status: 'running',
    startTime: '2026-03-11T10:05:00',
    endTime: null,
    durationSeconds: null,
    rowsOutput: 0,
    errorMessage: null,
    logUrl: null,
    triggerType: 'manual',
    createdAt: '2026-03-11T10:05:00',
    updatedAt: '2026-03-11T10:05:00',
    workflowCode: null,
    workflowName: 'README 演示 - 订单主题加工链路',
    taskCode: 'readme_demo_build_store_sales_daily',
    workflowInstanceUrl: null,
    taskDefinitionUrl: null,
    dolphinInstanceId: null,
    dolphinState: null,
    dolphinStartTime: null,
    dolphinEndTime: null,
    dolphinDuration: null,
    runTimes: 1,
    host: 'demo-worker-01',
    commandType: 'COMPLEMENT_DATA'
  },
  {
    id: 2,
    taskId: 2,
    executionId: 'local-demo-810001-00',
    status: 'success',
    startTime: '2026-03-10T10:05:00',
    endTime: '2026-03-10T10:07:20',
    durationSeconds: 140,
    rowsOutput: 3,
    errorMessage: null,
    logUrl: null,
    triggerType: 'schedule',
    createdAt: '2026-03-10T10:07:20',
    updatedAt: '2026-03-10T10:07:20',
    workflowCode: null,
    workflowName: 'README 演示 - 订单主题加工链路',
    taskCode: 'readme_demo_build_store_sales_daily',
    workflowInstanceUrl: null,
    taskDefinitionUrl: null,
    dolphinInstanceId: null,
    dolphinState: null,
    dolphinStartTime: null,
    dolphinEndTime: null,
    dolphinDuration: null,
    runTimes: 1,
    host: 'demo-worker-01',
    commandType: 'SCHEDULER'
  },
  {
    id: 1,
    taskId: 1,
    executionId: 'local-demo-810001-01',
    status: 'success',
    startTime: '2026-03-11T09:30:00',
    endTime: '2026-03-11T09:32:40',
    durationSeconds: 160,
    rowsOutput: 5,
    errorMessage: null,
    logUrl: null,
    triggerType: 'schedule',
    createdAt: '2026-03-11T09:32:40',
    updatedAt: '2026-03-11T09:32:40',
    workflowCode: null,
    workflowName: 'README 演示 - 订单主题加工链路',
    taskCode: 'readme_demo_build_order_detail',
    workflowInstanceUrl: null,
    taskDefinitionUrl: null,
    dolphinInstanceId: null,
    dolphinState: null,
    dolphinStartTime: null,
    dolphinEndTime: null,
    dolphinDuration: null,
    runTimes: 1,
    host: 'demo-worker-01',
    commandType: 'SCHEDULER'
  }
]

const businessDomainOptions = [
  {
    id: 1,
    domainCode: 'tech',
    domainName: '技术域',
    description: 'README 演示业务域'
  }
]

const dataDomainOptions = [
  { id: 1, domainCode: 'dev', domainName: '研发域', businessDomain: 'tech', description: '研发相关元数据' },
  { id: 2, domainCode: 'ops', domainName: '运维域', businessDomain: 'tech', description: '任务调度与治理相关数据' },
  { id: 3, domainCode: 'public', domainName: '公共域', businessDomain: 'tech', description: '公共维度与字典数据' }
]
const baseQueryHistory = [
  {
    id: 90003,
    clusterId: DEMO_CLUSTER_ID,
    clusterName: 'README 演示集群',
    databaseName: DEMO_DATABASE,
    sqlText: 'SELECT city_name, SUM(order_amount) AS total_amount\nFROM `opendataworks`.`demo_order_detail`\nGROUP BY city_name\nORDER BY total_amount DESC;',
    previewRowCount: 4,
    durationMs: 24,
    hasMore: 0,
    resultPreview: JSON.stringify({
      columns: ['city_name', 'total_amount'],
      rows: [
        { city_name: '南京', total_amount: 699.0 },
        { city_name: '杭州', total_amount: 326.5 },
        { city_name: '上海', total_amount: 247.9 },
        { city_name: '苏州', total_amount: 88.0 }
      ]
    }),
    executedBy: 'demo',
    executedAt: '2026-03-11T14:10:00'
  },
  {
    id: 90002,
    clusterId: DEMO_CLUSTER_ID,
    clusterName: 'README 演示集群',
    databaseName: DEMO_DATABASE,
    sqlText: 'SELECT *\nFROM `opendataworks`.`demo_store_sales_daily`\nLIMIT 200;',
    previewRowCount: 3,
    durationMs: 18,
    hasMore: 0,
    resultPreview: JSON.stringify({
      columns: ['stat_date', 'store_id', 'paid_order_cnt', 'paid_order_amount'],
      rows: tableRows.demo_store_sales_daily
    }),
    executedBy: 'demo',
    executedAt: '2026-03-11T14:06:00'
  },
  {
    id: 90001,
    clusterId: DEMO_CLUSTER_ID,
    clusterName: 'README 演示集群',
    databaseName: DEMO_DATABASE,
    sqlText: 'SELECT *\nFROM `opendataworks`.`demo_order_detail`\nLIMIT 200;',
    previewRowCount: 5,
    durationMs: 8,
    hasMore: 0,
    resultPreview: JSON.stringify({
      columns: ['order_id', 'member_id', 'store_id', 'city_name', 'member_level', 'order_amount', 'order_date', 'pay_status'],
      rows: tableRows.demo_order_detail
    }),
    executedBy: 'demo',
    executedAt: '2026-03-11T14:02:00'
  }
]

const tableTaskMap = {
  1232: { writeTasks: [], readTasks: [baseTasks[2]] },
  1233: { writeTasks: [], readTasks: [baseTasks[2]] },
  1234: { writeTasks: [baseTasks[2]], readTasks: [baseTasks[0], baseTasks[1]] },
  1235: { writeTasks: [baseTasks[1]], readTasks: [] },
  1236: { writeTasks: [baseTasks[0]], readTasks: [] }
}

const lineageEdges = [
  { source: 1232, target: 1234, taskId: 1 },
  { source: 1233, target: 1234, taskId: 1 },
  { source: 1234, target: 1235, taskId: 2 },
  { source: 1234, target: 1236, taskId: 3 }
]

const accessStatsMap = {
  1232: {
    tableId: 1232,
    clusterId: DEMO_CLUSTER_ID,
    databaseName: DEMO_DATABASE,
    tableName: 'demo_member_profile',
    totalAccessCount: 17,
    recentAccessCount: 5,
    accessCount7d: 12,
    accessCount30d: 17,
    lastAccessTime: '2026-03-11T14:08:00',
    firstAccessTime: '2026-03-10T09:30:00',
    distinctUserCount: 3,
    averageDurationMs: 19,
    recentDays: 30,
    trendDays: 14,
    trend: [
      { date: '2026-03-08', accessCount: 2 },
      { date: '2026-03-09', accessCount: 4 },
      { date: '2026-03-10', accessCount: 6 },
      { date: '2026-03-11', accessCount: 5 }
    ],
    topUsers: [
      { userId: 'readme', accessCount: 8, lastAccessTime: '2026-03-11T14:08:00' },
      { userId: 'analyst', accessCount: 5, lastAccessTime: '2026-03-11T11:32:00' },
      { userId: 'demo', accessCount: 4, lastAccessTime: '2026-03-10T17:10:00' }
    ],
    dorisAuditEnabled: true,
    dorisAuditSource: 'demo',
    note: ''
  },
  1234: {
    tableId: 1234,
    clusterId: DEMO_CLUSTER_ID,
    databaseName: DEMO_DATABASE,
    tableName: 'demo_order_detail',
    totalAccessCount: 36,
    recentAccessCount: 11,
    accessCount7d: 25,
    accessCount30d: 36,
    lastAccessTime: '2026-03-11T14:25:10',
    firstAccessTime: '2026-03-10T09:30:00',
    distinctUserCount: 4,
    averageDurationMs: 27,
    recentDays: 30,
    trendDays: 14,
    trend: [
      { date: '2026-03-08', accessCount: 4 },
      { date: '2026-03-09', accessCount: 5 },
      { date: '2026-03-10', accessCount: 9 },
      { date: '2026-03-11', accessCount: 11 }
    ],
    topUsers: [
      { userId: 'demo', accessCount: 12, lastAccessTime: '2026-03-11T14:25:10' },
      { userId: 'analyst', accessCount: 9, lastAccessTime: '2026-03-11T13:04:22' },
      { userId: 'readme', accessCount: 8, lastAccessTime: '2026-03-11T10:18:00' },
      { userId: 'bi', accessCount: 7, lastAccessTime: '2026-03-11T09:36:15' }
    ],
    dorisAuditEnabled: true,
    dorisAuditSource: 'demo',
    note: ''
  }
}

const statisticsHistoryMap = {
  1232: [
    { statisticsTime: '2026-03-08T00:00:00', rowCount: 4, dataSize: 8192 },
    { statisticsTime: '2026-03-09T00:00:00', rowCount: 4, dataSize: 8192 },
    { statisticsTime: '2026-03-10T00:00:00', rowCount: 4, dataSize: 8192 },
    { statisticsTime: '2026-03-11T00:00:00', rowCount: 4, dataSize: 8192 }
  ],
  1233: [
    { statisticsTime: '2026-03-08T00:00:00', rowCount: 5, dataSize: 12288 },
    { statisticsTime: '2026-03-09T00:00:00', rowCount: 5, dataSize: 12288 },
    { statisticsTime: '2026-03-10T00:00:00', rowCount: 5, dataSize: 12288 },
    { statisticsTime: '2026-03-11T00:00:00', rowCount: 5, dataSize: 12288 }
  ],
  1234: [
    { statisticsTime: '2026-03-08T00:00:00', rowCount: 5, dataSize: 12288 },
    { statisticsTime: '2026-03-09T00:00:00', rowCount: 5, dataSize: 14336 },
    { statisticsTime: '2026-03-10T00:00:00', rowCount: 5, dataSize: 16384 },
    { statisticsTime: '2026-03-11T00:00:00', rowCount: 5, dataSize: 16384 }
  ],
  1235: [
    { statisticsTime: '2026-03-08T00:00:00', rowCount: 3, dataSize: 6144 },
    { statisticsTime: '2026-03-09T00:00:00', rowCount: 3, dataSize: 7168 },
    { statisticsTime: '2026-03-10T00:00:00', rowCount: 3, dataSize: 8192 },
    { statisticsTime: '2026-03-11T00:00:00', rowCount: 3, dataSize: 8192 }
  ],
  1236: [
    { statisticsTime: '2026-03-08T00:00:00', rowCount: 1, dataSize: 2048 },
    { statisticsTime: '2026-03-09T00:00:00', rowCount: 1, dataSize: 2048 },
    { statisticsTime: '2026-03-10T00:00:00', rowCount: 2, dataSize: 4096 },
    { statisticsTime: '2026-03-11T00:00:00', rowCount: 2, dataSize: 4096 }
  ]
}

const clone = (value) => JSON.parse(JSON.stringify(value))

let queryHistoryState = clone(baseQueryHistory)
let queryHistorySeed = 91000

const getTables = () => clone(baseTables)
const getWorkflows = () => clone(baseWorkflows)
const getTasks = () => clone(baseTasks)
const getExecutions = () => clone(baseExecutions)

const getTableById = (id) => baseTables.find((item) => Number(item.id) === Number(id)) || null
const getTableByName = (tableName) => baseTables.find((item) => item.tableName === tableName) || null

const getTableRows = (tableName) => clone(tableRows[tableName] || [])
const getTableFields = (tableId) => clone(baseTableFields[Number(tableId)] || [])
const getTableTasks = (tableId) => clone(tableTaskMap[Number(tableId)] || { writeTasks: [], readTasks: [] })

const getLineageForTable = (tableId) => {
  const upstreamIds = lineageEdges.filter((item) => Number(item.target) === Number(tableId)).map((item) => item.source)
  const downstreamIds = lineageEdges.filter((item) => Number(item.source) === Number(tableId)).map((item) => item.target)
  return {
    upstreamTables: baseTables.filter((item) => upstreamIds.includes(item.id)).map((item) => ({ ...item })),
    downstreamTables: baseTables.filter((item) => downstreamIds.includes(item.id)).map((item) => ({ ...item }))
  }
}

const buildLineageGraph = (params = {}) => {
  const centerTableId = Number(params.tableId || 0)
  if (centerTableId) {
    const center = getTableById(centerTableId)
    if (!center) {
      return { nodes: [], edges: [] }
    }
    const relatedTableIds = new Set([center.id])
    lineageEdges.forEach((edge) => {
      if (edge.source === center.id || edge.target === center.id) {
        relatedTableIds.add(edge.source)
        relatedTableIds.add(edge.target)
      }
    })
    const nodes = baseTables
      .filter((item) => relatedTableIds.has(item.id))
      .map((item) => ({
        id: item.id,
        tableId: item.id,
        clusterId: item.clusterId,
        dbName: item.dbName,
        tableName: item.tableName,
        name: item.tableName,
        comment: item.tableComment,
        tableComment: item.tableComment,
        layer: item.layer,
        businessDomain: item.businessDomain,
        dataDomain: item.dataDomain,
        inDegree: lineageEdges.filter((edge) => edge.target === item.id).length,
        outDegree: lineageEdges.filter((edge) => edge.source === item.id).length
      }))
    const edges = lineageEdges.filter((item) => relatedTableIds.has(item.source) && relatedTableIds.has(item.target))
    return { nodes, edges }
  }

  let nodes = baseTables.filter((item) => {
    if (params.clusterId && Number(params.clusterId) !== item.clusterId) return false
    if (params.dbName && params.dbName !== item.dbName) return false
    if (params.layer && params.layer !== item.layer) return false
    if (params.businessDomain && params.businessDomain !== item.businessDomain) return false
    if (params.dataDomain && params.dataDomain !== item.dataDomain) return false
    if (params.keyword) {
      const keyword = String(params.keyword).toLowerCase()
      const haystacks = [item.tableName, item.tableComment, item.businessDomain, item.dataDomain]
      if (!haystacks.some((value) => String(value || '').toLowerCase().includes(keyword))) {
        return false
      }
    }
    return true
  })

  const nodeIds = new Set(nodes.map((item) => item.id))
  const edges = lineageEdges.filter((item) => nodeIds.has(item.source) && nodeIds.has(item.target))

  nodes = nodes.map((item) => ({
    id: item.id,
    tableId: item.id,
    clusterId: item.clusterId,
    dbName: item.dbName,
    tableName: item.tableName,
    name: item.tableName,
    comment: item.tableComment,
    tableComment: item.tableComment,
    layer: item.layer,
    businessDomain: item.businessDomain,
    dataDomain: item.dataDomain,
    inDegree: edges.filter((edge) => edge.target === item.id).length,
    outDegree: edges.filter((edge) => edge.source === item.id).length
  }))
  return { nodes, edges }
}

const toPaged = (records, pageNum = 1, pageSize = 10) => {
  const currentPage = Math.max(1, Number(pageNum) || 1)
  const currentSize = Math.max(1, Number(pageSize) || 10)
  const start = (currentPage - 1) * currentSize
  return {
    total: records.length,
    records: records.slice(start, start + currentSize)
  }
}

const parseData = (value) => {
  if (!value) return {}
  if (typeof value === 'string') {
    try {
      return JSON.parse(value)
    } catch (_) {
      return {}
    }
  }
  return value
}

const createResponse = (config, data, status = 200, statusText = 'OK') => Promise.resolve({
  data: {
    code: 200,
    message: 'success',
    data
  },
  status,
  statusText,
  headers: {},
  config,
  request: {}
})

const createRejectedResponse = (config, message, status = 400) => {
  const error = new Error(message)
  error.config = config
  error.response = {
    status,
    data: {
      code: status,
      message
    },
    config,
    headers: {}
  }
  return Promise.reject(error)
}

const createCanceledResponse = (config) => {
  const error = new Error('canceled')
  error.code = 'ERR_CANCELED'
  error.name = 'CanceledError'
  error.config = config
  return Promise.reject(error)
}

const parseRequestUrl = (config) => {
  const url = new URL(config.url || '/', 'https://demo.local')
  const params = new URLSearchParams(url.search)
  Object.entries(config.params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    params.set(key, String(value))
  })
  const paramObject = {}
  params.forEach((value, key) => {
    paramObject[key] = value
  })
  return {
    method: String(config.method || 'get').toLowerCase(),
    pathname: url.pathname,
    params: paramObject,
    body: parseData(config.data)
  }
}

const getPreviewPayload = (tableName, limit = 200) => {
  const rows = getTableRows(tableName).slice(0, Math.max(1, Number(limit) || 200))
  const columns = rows.length ? Object.keys(rows[0]) : getTableFields(getTableByName(tableName)?.id || 0).map((item) => item.fieldName)
  return {
    columns,
    rows
  }
}

const abbreviateSql = (sql) => String(sql || '').trim().replace(/\s+/g, ' ').slice(0, 120)

const splitStatements = (sql) => {
  return String(sql || '')
    .split(';')
    .map((item) => item.trim())
    .filter(Boolean)
}

const inferSqlType = (sql) => {
  const normalized = String(sql || '').trim().toUpperCase()
  if (normalized.startsWith('SELECT')) return 'SELECT'
  if (normalized.startsWith('INSERT')) return 'INSERT'
  if (normalized.startsWith('UPDATE')) return 'UPDATE'
  if (normalized.startsWith('DELETE')) return 'DELETE'
  if (normalized.startsWith('CREATE')) return 'CREATE'
  if (normalized.startsWith('DROP')) return 'DROP'
  return 'UNKNOWN'
}

const extractTableNameFromSql = (sql) => {
  const text = String(sql || '')
  const explicitMatch = text.match(/from\s+`([^`]+)`\.`([^`]+)`/i)
  if (explicitMatch) {
    return explicitMatch[2]
  }
  const simpleMatch = text.match(/from\s+([a-zA-Z0-9_]+)/i)
  if (simpleMatch) {
    return simpleMatch[1]
  }
  return ''
}

const buildStatementPreview = (statement, statementIndex) => {
  const sqlType = inferSqlType(statement)
  const blocked = sqlType !== 'SELECT'
  return {
    statementIndex,
    sqlSnippet: abbreviateSql(statement),
    sqlType,
    riskLevel: blocked ? 'HIGH' : 'LOW',
    parseStatus: blocked ? 'PARSED' : 'SKIPPED',
    requiresConfirm: false,
    targetObject: extractTableNameFromSql(statement) || null,
    blocked,
    blockedReason: blocked ? '演示环境仅支持 SELECT 查询' : null
  }
}

const buildAnalyzePayload = (body) => {
  const statements = splitStatements(body.sql)
  const riskItems = statements.map((statement, index) => buildStatementPreview(statement, index + 1))
  return {
    statements: statements.map((statement, index) => ({
      statementIndex: index + 1,
      sqlSnippet: abbreviateSql(statement),
      sqlType: inferSqlType(statement)
    })),
    riskItems,
    confirmChallenges: [],
    blocked: riskItems.some((item) => item.blocked),
    blockedReason: riskItems.find((item) => item.blocked)?.blockedReason || null
  }
}

const aggregateByCity = () => {
  const map = new Map()
  tableRows.demo_order_detail.forEach((row) => {
    const current = map.get(row.city_name) || { city_name: row.city_name, total_amount: 0, total_orders: 0 }
    current.total_amount += Number(row.order_amount || 0)
    current.total_orders += 1
    map.set(row.city_name, current)
  })
  return Array.from(map.values()).sort((a, b) => b.total_amount - a.total_amount)
}

const aggregateByStore = () => {
  const map = new Map()
  tableRows.demo_order_detail.forEach((row) => {
    const current = map.get(row.store_id) || { store_id: row.store_id, order_cnt: 0, total_amount: 0 }
    current.order_cnt += 1
    current.total_amount += Number(row.order_amount || 0)
    map.set(row.store_id, current)
  })
  return Array.from(map.values()).sort((a, b) => Number(a.store_id) - Number(b.store_id))
}

const buildSelectResult = (statement, limit) => {
  const lower = String(statement).toLowerCase()
  if (lower.includes('from `opendataworks`.`demo_order_detail`') && lower.includes('group by city_name')) {
    const rows = aggregateByCity()
    return {
      columns: ['city_name', 'total_amount', 'total_orders'],
      rows: rows.slice(0, limit),
      message: '执行成功'
    }
  }
  if (lower.includes('from `opendataworks`.`demo_order_detail`') && lower.includes('group by store_id')) {
    const rows = aggregateByStore()
    return {
      columns: ['store_id', 'order_cnt', 'total_amount'],
      rows: rows.slice(0, limit),
      message: '执行成功'
    }
  }

  const tableName = extractTableNameFromSql(statement)
  const table = getTableByName(tableName)
  if (!table) {
    return {
      columns: ['message'],
      rows: [{ message: '未匹配到样例表，请从左侧样例表生成查询。' }],
      message: '已返回演示提示'
    }
  }

  return {
    ...getPreviewPayload(table.tableName, limit),
    message: '执行成功'
  }
}

const buildExecutePayload = (body) => {
  const statements = splitStatements(body.sql)
  const limit = Math.max(1, Number(body.limit) || 200)
  const executedAt = '2026-03-11T14:25:10.149'
  const resultSets = statements.map((statement, index) => {
    const sqlType = inferSqlType(statement)
    if (sqlType !== 'SELECT') {
      return {
        index: index + 1,
        statementIndex: index + 1,
        status: 'BLOCKED',
        resultType: 'NONE',
        columns: [],
        rows: [],
        previewRowCount: 0,
        hasMore: false,
        affectedRows: null,
        message: '演示环境仅支持 SELECT 查询',
        sqlSnippet: abbreviateSql(statement),
        durationMs: 0
      }
    }

    const result = buildSelectResult(statement, limit)
    return {
      index: index + 1,
      statementIndex: index + 1,
      status: 'SUCCESS',
      resultType: 'RESULT_SET',
      columns: result.columns,
      rows: result.rows,
      previewRowCount: result.rows.length,
      hasMore: false,
      affectedRows: null,
      message: result.message,
      sqlSnippet: abbreviateSql(statement),
      durationMs: 8 + index * 4
    }
  })

  const firstResultSet = resultSets.find((item) => item.status === 'SUCCESS') || {
    columns: [],
    rows: []
  }
  const successCount = resultSets.filter((item) => item.status === 'SUCCESS').length
  const blockedCount = resultSets.filter((item) => item.status === 'BLOCKED').length
  const historyEntry = {
    id: ++queryHistorySeed,
    clusterId: Number(body.clusterId) || DEMO_CLUSTER_ID,
    clusterName: 'README 演示集群',
    databaseName: body.database || DEMO_DATABASE,
    sqlText: body.sql,
    previewRowCount: firstResultSet.rows.length,
    durationMs: 56,
    hasMore: 0,
    resultPreview: JSON.stringify({
      columns: firstResultSet.columns,
      rows: firstResultSet.rows
    }),
    executedBy: 'demo',
    executedAt
  }
  queryHistoryState = [historyEntry, ...queryHistoryState].slice(0, 20)

  return {
    resultSets,
    resultSetCount: resultSets.length,
    cancelled: false,
    message: `执行完成：成功 ${successCount}，阻断 ${blockedCount}，失败 0，跳过 0`,
    columns: firstResultSet.columns,
    rows: firstResultSet.rows,
    previewRowCount: firstResultSet.rows.length,
    hasMore: false,
    durationMs: 56,
    historyId: historyEntry.id,
    executedAt
  }
}

const handleWorkflowList = (params) => {
  let records = getWorkflows()
  if (params.keyword) {
    const keyword = String(params.keyword).toLowerCase()
    records = records.filter((item) => item.workflowName.toLowerCase().includes(keyword))
  }
  if (params.status) {
    records = records.filter((item) => item.status === params.status)
  }
  return toPaged(records, params.pageNum, params.pageSize)
}

const handleTaskList = (params) => {
  let records = getTasks()
  if (params.taskType) {
    records = records.filter((item) => item.taskType === params.taskType)
  }
  if (params.status) {
    records = records.filter((item) => item.status === params.status)
  }
  if (params.taskName) {
    const keyword = String(params.taskName).toLowerCase()
    records = records.filter((item) => item.taskName.toLowerCase().includes(keyword))
  }
  if (params.workflowId) {
    records = records.filter((item) => Number(item.workflowId) === Number(params.workflowId))
  }
  if (params.upstreamTaskId) {
    const upstreamId = Number(params.upstreamTaskId)
    records = records.filter((item) => {
      if (upstreamId === 1) return item.id === 2
      return false
    })
  }
  if (params.downstreamTaskId) {
    const downstreamId = Number(params.downstreamTaskId)
    records = records.filter((item) => {
      if (downstreamId === 2) return item.id === 1
      return false
    })
  }
  return toPaged(records, params.pageNum, params.pageSize)
}

const filterExecutions = (params = {}) => {
  let records = getExecutions()
  if (params.taskId) {
    records = records.filter((item) => Number(item.taskId) === Number(params.taskId))
  }
  if (params.startTime) {
    records = records.filter((item) => !item.startTime || item.startTime >= params.startTime)
  }
  if (params.endTime) {
    records = records.filter((item) => !item.startTime || item.startTime <= params.endTime)
  }
  return records
}

const handleExecutionStats = (params) => {
  const records = filterExecutions(params)
  const totalExecutions = records.length
  const successCount = records.filter((item) => item.status === 'success').length
  const failedCount = records.filter((item) => item.status === 'failed').length
  const finished = records.filter((item) => typeof item.durationSeconds === 'number')
  const avgDurationSeconds = finished.length
    ? Math.round(finished.reduce((sum, item) => sum + Number(item.durationSeconds || 0), 0) / finished.length)
    : 0
  return {
    totalExecutions,
    successCount,
    failedCount,
    failureRate: totalExecutions ? Number(((failedCount / totalExecutions) * 100).toFixed(2)) : 0,
    successRate: totalExecutions ? Number(((successCount / totalExecutions) * 100).toFixed(2)) : 0,
    avgDurationSeconds,
    trend: [
      { statDate: '2026-03-10', totalCount: 2, successCount: 2, failedCount: 0 },
      { statDate: '2026-03-11', totalCount: 4, successCount: 2, failedCount: 1 }
    ]
  }
}

const toDashboardDate = (value) => {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const daysSince = (value) => {
  const target = toDashboardDate(value)
  if (!target) return 999
  const now = new Date('2026-03-11T23:59:59')
  return Math.max(0, Math.floor((now.getTime() - target.getTime()) / (24 * 60 * 60 * 1000)))
}

const handleDashboardStatistics = (params = {}) => {
  const clusterId = params.clusterId ? Number(params.clusterId) : null
  const tables = getTables().filter((item) => !clusterId || item.clusterId === clusterId)
  const tasks = getTasks()
  const executions = filterExecutions({})

  const hotTables = tables
    .map((item) => {
      const stats = accessStatsMap[item.id] || {}
      return {
        dbName: item.dbName,
        tableName: item.tableName,
        accessCount: Number(stats.accessCount30d || stats.totalAccessCount || stats.recentAccessCount || 0),
        lastAccessTime: stats.lastAccessTime || null
      }
    })
    .sort((left, right) => right.accessCount - left.accessCount || String(left.tableName).localeCompare(String(right.tableName)))
    .slice(0, 5)

  const longUnusedTables = tables
    .map((item) => {
      const stats = accessStatsMap[item.id] || {}
      const lastAccessTime = stats.lastAccessTime || null
      return {
        dbName: item.dbName,
        tableName: item.tableName,
        lastAccessTime,
        daysSinceLastAccess: lastAccessTime ? daysSince(lastAccessTime) : 120
      }
    })
    .sort((left, right) => right.daysSinceLastAccess - left.daysSinceLastAccess || String(left.tableName).localeCompare(String(right.tableName)))
    .slice(0, 5)

  const totalExecutions = executions.length
  const successExecutions = executions.filter((item) => item.status === 'success').length
  const failedExecutions = executions.filter((item) => item.status === 'failed').length
  const runningExecutions = executions.filter((item) => item.status === 'running').length
  const todayExecutions = executions.filter((item) => String(item.startTime || '').startsWith('2026-03-11')).length
  const todaySuccessExecutions = executions.filter((item) => item.status === 'success' && String(item.startTime || '').startsWith('2026-03-11')).length
  const todayFailedExecutions = executions.filter((item) => item.status === 'failed' && String(item.startTime || '').startsWith('2026-03-11')).length

  return {
    totalTables: tables.length,
    totalDomains: dataDomainOptions.length,
    tableAccessNote: '演示环境展示样例访问统计数据。',
    hotTables,
    hotWindowDays: 30,
    longUnusedTables,
    coldWindowDays: 90,
    totalTasks: tasks.length,
    totalExecutions,
    runningExecutions,
    openIssues: 2,
    criticalIssues: 1,
    successExecutions,
    executionSuccessRate: totalExecutions ? Number(((successExecutions / totalExecutions) * 100).toFixed(2)) : 0,
    failedExecutions,
    todayExecutions,
    todaySuccessExecutions,
    todayFailedExecutions
  }
}
const handleTablesByDatabase = (params) => {
  let records = getTables()
  if (params.database) {
    records = records.filter((item) => item.dbName === params.database)
  }
  records.sort((a, b) => String(a.tableName).localeCompare(String(b.tableName)))
  if (params.sortField && params.sortField !== 'tableName') {
    const direction = params.sortOrder === 'desc' ? -1 : 1
    records.sort((a, b) => {
      const left = a[params.sortField] ?? ''
      const right = b[params.sortField] ?? ''
      if (left === right) return 0
      return left > right ? direction : -direction
    })
  }
  return records
}

const handleTableOptions = (params) => {
  const keyword = String(params.keyword || '').trim().toLowerCase()
  let records = getTables()
  if (params.clusterId) {
    records = records.filter((item) => Number(item.clusterId) === Number(params.clusterId))
  }
  if (params.dbName) {
    records = records.filter((item) => item.dbName === params.dbName)
  }
  if (keyword) {
    records = records.filter((item) => {
      return [item.tableName, item.tableComment, item.layer]
        .some((value) => String(value || '').toLowerCase().includes(keyword))
    })
  }
  const limit = Math.max(1, Number(params.limit) || 20)
  return records.slice(0, limit)
}

const handleQueryHistory = (params) => {
  let records = clone(queryHistoryState)
  if (params.clusterId) {
    records = records.filter((item) => Number(item.clusterId) === Number(params.clusterId))
  }
  if (params.databaseName) {
    records = records.filter((item) => item.databaseName === params.databaseName)
  }
  return {
    ...toPaged(records, params.pageNum, params.pageSize),
    size: Math.max(1, Number(params.pageSize) || 20),
    current: Math.max(1, Number(params.pageNum) || 1),
    pages: Math.ceil(records.length / Math.max(1, Number(params.pageSize) || 20))
  }
}

export const demoAdapter = async (config) => {
  if (config.signal?.aborted) {
    return createCanceledResponse(config)
  }

  const { method, pathname, params, body } = parseRequestUrl(config)

  if (method === 'get' && pathname === '/v1/tasks/config/dolphin-webui') {
    return createResponse(config, { webuiUrl: '' })
  }

  if (method === 'get' && pathname === '/v1/dashboard/statistics') {
    return createResponse(config, handleDashboardStatistics(params))
  }
  if (method === 'get' && pathname === '/v1/workflows') {
    return createResponse(config, handleWorkflowList(params))
  }

  if (method === 'get' && pathname === '/v1/tasks') {
    return createResponse(config, handleTaskList(params))
  }

  if (method === 'get' && pathname === '/v1/executions/statistics') {
    return createResponse(config, handleExecutionStats(params))
  }

  if (method === 'get' && pathname === '/v1/executions/history') {
    return createResponse(config, toPaged(filterExecutions(params), params.pageNum, params.pageSize))
  }

  if (method === 'get' && pathname === '/v1/executions/running') {
    return createResponse(config, filterExecutions({}).filter((item) => item.status === 'running'))
  }

  if (method === 'get' && pathname === '/v1/executions/failed') {
    const limit = Math.max(1, Number(params.limit) || 50)
    return createResponse(config, filterExecutions({}).filter((item) => item.status === 'failed').slice(0, limit))
  }

  if (method === 'post' && pathname.match(/^\/v1\/executions\/\d+\/sync$/)) {
    return createResponse(config, true)
  }

  if (method === 'get' && pathname.match(/^\/v1\/executions\/\d+$/)) {
    const executionId = Number(pathname.split('/').pop())
    const execution = getExecutions().find((item) => item.id === executionId)
    return execution
      ? createResponse(config, execution)
      : createRejectedResponse(config, '执行记录不存在', 404)
  }

  if (method === 'get' && pathname === '/v1/doris-clusters') {
    return createResponse(config, [
      {
        id: DEMO_CLUSTER_ID,
        clusterName: 'README 演示集群',
        sourceType: 'DORIS',
        feHost: 'demo-doris.local',
        fePort: 9030,
        isDefault: 1,
        status: 'active'
      }
    ])
  }

  if (method === 'post' && pathname.match(/^\/v1\/doris-clusters\/\d+\/test$/)) {
    return createResponse(config, true)
  }

  if (method === 'get' && pathname.match(/^\/v1\/doris-clusters\/\d+\/schema-object-counts$/)) {
    return createResponse(config, [
      {
        schemaName: DEMO_DATABASE,
        tableCount: 5,
        viewCount: 0,
        totalCount: 5
      }
    ])
  }

  if (method === 'get' && pathname.match(/^\/v1\/doris-clusters\/\d+\/databases$/)) {
    return createResponse(config, [DEMO_DATABASE])
  }

  if (method === 'get' && pathname.match(/^\/v1\/doris-clusters\/\d+\/databases\/[^/]+\/tables$/)) {
    const tables = getTables().map((item) => ({
      tableType: item.tableType,
      createTime: item.dorisCreateTime,
      dataLength: item.storageSize,
      tableComment: item.tableComment,
      updateTime: item.dorisUpdateTime,
      tableName: item.tableName,
      tableRows: item.rowCount
    }))
    return createResponse(config, tables)
  }

  if (method === 'get' && pathname === '/v1/business-domains') {
    return createResponse(config, clone(businessDomainOptions))
  }

  if (method === 'get' && pathname === '/v1/data-domains') {
    const filtered = params.businessDomain
      ? dataDomainOptions.filter((item) => item.businessDomain === params.businessDomain)
      : dataDomainOptions
    return createResponse(config, filtered)
  }

  if (method === 'get' && pathname === '/v1/tables/databases') {
    return createResponse(config, [DEMO_DATABASE])
  }

  if (method === 'get' && pathname === '/v1/tables/by-database') {
    return createResponse(config, handleTablesByDatabase(params))
  }

  if (method === 'get' && pathname === '/v1/tables/options') {
    return createResponse(config, handleTableOptions(params))
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+$/)) {
    const tableId = Number(pathname.split('/').pop())
    const table = getTableById(tableId)
    return table
      ? createResponse(config, clone(table))
      : createRejectedResponse(config, '表不存在', 404)
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/fields$/)) {
    const tableId = Number(pathname.split('/')[3])
    return createResponse(config, getTableFields(tableId))
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/tasks$/)) {
    const tableId = Number(pathname.split('/')[3])
    return createResponse(config, getTableTasks(tableId))
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/lineage$/)) {
    const tableId = Number(pathname.split('/')[3])
    const lineage = getLineageForTable(tableId)
    return createResponse(config, lineage)
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/ddl$/)) {
    const tableId = Number(pathname.split('/')[3])
    const table = getTableById(tableId)
    return table
      ? createResponse(config, table.dorisDdl)
      : createRejectedResponse(config, '表不存在', 404)
  }

  if (method === 'get' && pathname === '/v1/tables/ddl/by-name') {
    const table = getTableByName(params.tableName)
    return table
      ? createResponse(config, table.dorisDdl)
      : createRejectedResponse(config, '表不存在', 404)
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/preview$/)) {
    const tableId = Number(pathname.split('/')[3])
    const table = getTableById(tableId)
    return table
      ? createResponse(config, getPreviewPayload(table.tableName, params.limit))
      : createRejectedResponse(config, '表不存在', 404)
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/access-stats$/)) {
    const tableId = Number(pathname.split('/')[3])
    const payload = accessStatsMap[tableId] || {
      tableId,
      clusterId: DEMO_CLUSTER_ID,
      databaseName: DEMO_DATABASE,
      tableName: getTableById(tableId)?.tableName || '',
      totalAccessCount: 0,
      recentAccessCount: 0,
      accessCount7d: 0,
      accessCount30d: 0,
      lastAccessTime: null,
      firstAccessTime: null,
      distinctUserCount: 0,
      averageDurationMs: null,
      recentDays: Number(params.recentDays) || 30,
      trendDays: Number(params.trendDays) || 14,
      trend: [],
      topUsers: [],
      dorisAuditEnabled: false,
      dorisAuditSource: null,
      note: '当前样例表尚未生成访问统计。'
    }
    return createResponse(config, clone(payload))
  }

  if (method === 'get' && pathname.match(/^\/v1\/tables\/\d+\/statistics\/history$/)) {
    const tableId = Number(pathname.split('/')[3])
    const limit = Math.max(1, Number(params.limit) || 30)
    return createResponse(config, clone((statisticsHistoryMap[tableId] || []).slice(-limit)))
  }

  if (method === 'get' && pathname === '/v1/lineage') {
    return createResponse(config, buildLineageGraph(params))
  }

  if (method === 'post' && pathname === '/v1/data-query/analyze') {
    return createResponse(config, buildAnalyzePayload(body))
  }

  if (method === 'post' && pathname === '/v1/data-query/execute') {
    return createResponse(config, buildExecutePayload(body))
  }

  if (method === 'post' && pathname === '/v1/data-query/stop') {
    return createResponse(config, { cancelled: true })
  }

  if (method === 'get' && pathname === '/v1/data-query/history') {
    return createResponse(config, handleQueryHistory(params))
  }

  if (['post', 'put', 'delete', 'patch'].includes(method)) {
    return createRejectedResponse(config, '演示环境仅支持浏览与查询')
  }

  return createRejectedResponse(config, `未实现的演示接口：${method.toUpperCase()} ${pathname}`, 404)
}
