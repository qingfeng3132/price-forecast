
DROP TABLE IF EXISTS goods_category;
CREATE TABLE goods_category(
  id               BIGINT           NOT NULL   AUTO_INCREMENT               COMMENT '分类主键',
  category_name    VARCHAR(50)      NOT NULL                                COMMENT '分类名称',
  category_code    VARCHAR(32)      NOT NULL                                COMMENT '分类编码（唯一）',
  create_time      DATETIME         NOT NULL   DEFAULT CURRENT_TIMESTAMP    COMMENT '创建时间',
  description      VARCHAR(200)     DEFAULT NULL                            COMMENT '分类描述',
  PRIMARY KEY(id),
  UNIQUE KEY uk_category_code(category_code)
  )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';


DROP TABLE IF EXISTS goods;
CREATE TABLE goods(
  id                BIGINT          NOT NULL   AUTO_INCREMENT               COMMENT '主键',
  goods_code        VARCHAR(32)     NOT NULL                                COMMENT '商品编号（唯一）',
  goods_name        VARCHAR(50)     NOT NULL                                COMMENT '商品名称，如：小麦、猪肉、包菜',
  category_id       BIGINT          NOT NULL                                COMMENT '所属分类，关联goods_category.id',
  source_platform   VARCHAR(50)     DEFAULT NULL                            COMMENT '数据来源平台',
  update_frequency  VARCHAR(20)     DEFAULT NULL                            COMMENT '数据更新频率，如：每日、每小时',
  create_time       DATETIME        NOT NULL    DEFAULT CURRENT_TIMESTAMP   COMMENT '创建时间',
  PRIMARY KEY(id),
  UNIQUE KEY uk_goods_code(goods_code)
  )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品信息表';


DROP TABLE IF EXISTS price_data;
CREATE TABLE price_data(
  id               BIGINT           NOT NULL   AUTO_INCREMENT               COMMENT '主键',
  goods_id         BIGINT           NOT NULL                                COMMENT '关联goods.id',
  price            DECIMAL(14,4)    NOT NULL                                COMMENT '价格',
  price_unit       VARCHAR(20)      NOT NULL                                COMMENT '价格单位：元/公斤、元/吨',
  price_date       DATE             NOT NULL                                COMMENT '价格对应日期',
  change_rate      DECIMAL(8,4)     DEFAULT NULL                            COMMENT '涨跌幅（%）',
  source_url       VARCHAR(255)     DEFAULT NULL                            COMMENT '数据来源 URL',
  crawl_time       DATETIME         NOT NULL     DEFAULT CURRENT_TIMESTAMP  COMMENT '抓取时间',
  PRIMARY KEY(id),
  UNIQUE KEY uk_goods_date(goods_id,price_date)
  )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='价格数据表';


DROP TABLE IF EXISTS forecast;
CREATE TABLE forecast(
  id               BIGINT           NOT NULL   AUTO_INCREMENT               COMMENT '主键',
  goods_id         BIGINT           NOT NULL                                COMMENT '关联goods.id',
  forecast_date    DATE             NOT NULL                                COMMENT '预测的日期',
  forecast_price   DECIMAL(14,4)    NOT NULL                                COMMENT '预测的价格',
  model_name       VARCHAR(50)      NOT NULL                                COMMENT '预测模型的名称',
  confidence        DECIMAL(5,4)    DEFAULT NULL                            COMMENT '置信度',
  basis_summary    TEXT             DEFAULT NULL                            COMMENT '预测依据摘要',
  create_time      DATETIME         NOT NULL      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY(id),
  UNIQUE KEY uk_goods_model_date(goods_id,model_name,forecast_date)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预测结果表';


DROP TABLE IF EXISTS query_log;
CREATE TABLE query_log(
  id               BIGINT           NOT NULL   AUTO_INCREMENT               COMMENT '主键',
  user_id          VARCHAR(64)      DEFAULT NULL                            COMMENT '用户标记',
  session_id       VARCHAR(64)      DEFAULT NULL                            COMMENT '会话标记（多轮对话）',
  query_content    TEXT             NOT NULL                                COMMENT '查询内容',
  intent_type      VARCHAR(30)      DEFAULT NULL                            COMMENT '查询意图分类：趋势/原因/对比/预测',
  response_time_ms INT              DEFAULT NULL                            COMMENT '响应时间',
  create_time      DATETIME         NOT NULL   DEFAULT CURRENT_TIMESTAMP    COMMENT '创建时间',
  PRIMARY KEY(id)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户查询记录表';


DROP TABLE IF EXISTS price_alert;
CREATE TABLE price_alert(
  id               BIGINT           NOT NULL   AUTO_INCREMENT               COMMENT '主键',
  goods_id         BIGINT           NOT NULL                                COMMENT '关联goods.id',
  alert_type       VARCHAR(10)      NOT NULL                                COMMENT '告警类型：上涨/下跌',
  change_rate      DECIMAL(8,4)     NOT NULL                                COMMENT '触发时的变化率（%）',
  threshold        DECIMAL(8,4)     NOT NULL                                COMMENT '触发时的阈值（%），快照',
  alert_status     VARCHAR(10)      NOT NULL     DEFAULT '未处理'            COMMENT '告警状态：未处理/已处理/已忽略',
  notify_channel   VARCHAR(20)      DEFAULT NULL                            COMMENT '通知渠道：站内消息/邮件/企业微信',
  notify_status    VARCHAR(10)      DEFAULT NULL                            COMMENT '通知状态',
  create_time      DATETIME         NOT NULL  DEFAULT CURRENT_TIMESTAMP     COMMENT '告警时间',
  handle_time      DATETIME         DEFAULT NULL                            COMMENT '处理时间',
  alert_date       DATE             NOT NULL                                COMMENT '告警日期（防抖设计）',
  PRIMARY KEY(id),
  UNIQUE KEY uk_goods_type_date(goods_id,alert_type,alert_date)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='价格告警记录表';


DROP TABLE IF EXISTS alert_threshold;
CREATE TABLE alert_threshold(
  id               BIGINT           NOT NULL   AUTO_INCREMENT               COMMENT '主键',
  goods_id         BIGINT           NOT NULL                                COMMENT '关联goods.id',
  up_threshold     DECIMAL(8,4)     NOT NULL   DEFAULT 10.0000              COMMENT '上涨预警阈值（%）',
  down_threshold   DECIMAL(8,4)     NOT NULL   DEFAULT 10.0000              COMMENT '下跌预警阈值（%）',
  create_time      DATETIME         NOT NULL   DEFAULT CURRENT_TIMESTAMP    COMMENT '创建时间',
  update_time      DATETIME         NULL                                    COMMENT '更新时间',
  PRIMARY KEY(id),
  UNIQUE KEY uk_goods(goods_id)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预警阈值配置表';