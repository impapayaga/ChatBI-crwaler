import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_database_schema():
    """从环境变量获取数据库建表语句"""
    return os.getenv("DATABASE_SCHEMA", get_default_schema())

def get_default_schema():
    """默认的数据库建表语句"""
    return """珠海高新区人口概览信息流水表:CREATE TABLE "public"."pl_mobile_people_flow_data" (
  "id" int4 NOT NULL DEFAULT nextval('mobile_people_id_seq'::regclass),
  "all_count" int4,
  "in_count" int4,
  "out_count" int4,
  "statistics_date" date,
  "activation" float4 DEFAULT 0,
  "base_line_value" float4 DEFAULT 0,
  CONSTRAINT "pl_mobile_people_flow_data_pkey" PRIMARY KEY ("id")
)
WITH (fillfactor=80)
;

ALTER TABLE "public"."pl_mobile_people_flow_data" 
  OWNER TO "postgres";

COMMENT ON COLUMN "public"."pl_mobile_people_flow_data"."all_count" IS '高新区日人流量';

COMMENT ON COLUMN "public"."pl_mobile_people_flow_data"."in_count" IS '进高新区';

COMMENT ON COLUMN "public"."pl_mobile_people_flow_data"."out_count" IS '出高新区';

COMMENT ON COLUMN "public"."pl_mobile_people_flow_data"."statistics_date" IS '统计日期';

COMMENT ON COLUMN "public"."pl_mobile_people_flow_data"."activation" IS '活跃度';

COMMENT ON COLUMN "public"."pl_mobile_people_flow_data"."base_line_value" IS '活跃度基线值';

COMMENT ON TABLE "public"."pl_mobile_people_flow_data" IS '生产生活-运营商人流监测';
珠海市高新区人口流动城市明细表:
CREATE TABLE "public"."mobile_day_flow_tag" (
  "id" int4 NOT NULL DEFAULT nextval('mobile_day_flow_tag_id_seq'::regclass),
  "area" varchar(50) COLLATE "pg_catalog"."default",
  "label_cnt" int4,
  "tag" varchar(50) COLLATE "pg_catalog"."default",
  "label" varchar(50) COLLATE "pg_catalog"."default",
  "type" int2,
  "day" varchar(10) COLLATE "pg_catalog"."default",
  "create_time" timestamp(6) DEFAULT now(),
  CONSTRAINT "mobile_day_flow_tag_pkey" PRIMARY KEY ("id")
)
WITH (fillfactor=80)
;

ALTER TABLE "mobile_day_flow_tag" 
  OWNER TO "postgres";

COMMENT ON COLUMN "public"."mobile_day_flow_tag"."label_cnt" IS '人数';

COMMENT ON COLUMN "public"."mobile_day_flow_tag"."tag" IS '标签类别，例如省外来源，省内来源，性别，年龄等';

COMMENT ON COLUMN "public"."mobile_day_flow_tag"."label" IS '标签名称，例如标签类别为省内来源时，标签名称为"珠海"';

COMMENT ON COLUMN "public"."mobile_day_flow_tag"."type" IS '1=日驻留、2=新流入、3=新流出';
珠海高新区年末常驻人口信息表:
CREATE TABLE "public"."pl_pop_trend_of_end_year" (
  "date_time" varchar(10) COLLATE "pg_catalog"."default" NOT NULL,
  "num" float4,
  "create_time" timestamp(6) DEFAULT now(),
  CONSTRAINT "pl_pop_trend_of_end_year_pkey" PRIMARY KEY ("date_time")
)
WITH (fillfactor=80)
;

ALTER TABLE "public"."pl_pop_trend_of_end_year" 
  OWNER TO "postgres";
COMMENT ON COLUMN "public"."pl_pop_trend_of_end_year"."num" IS '单位(万)';
COMMENT ON TABLE "public"."pl_pop_trend_of_end_year" IS '年末常驻人口变化趋势';
珠海高新区各社区人口年龄分布统计结果表:
CREATE TABLE "public"."grid_first_level_info" (
  "community" varchar(30) COLLATE "pg_catalog"."default" NOT NULL,
  "grid_leader" varchar(1000) COLLATE "pg_catalog"."default",
  "build_num" int4 DEFAULT 0,
  "population" int4 DEFAULT 0,
  "inconvenience_num" int4 DEFAULT 0,
  "disable_num" int4 DEFAULT 0,
  "other_pop_num" int4 DEFAULT 0,
  "geom" geometry(GEOMETRY),
  "overview" varchar(500) COLLATE "pg_catalog"."default",
  "area" float4,
  "resident_population" int4,
  "registered_population" int4,
  "total_population" int4,
  "location" varchar(50) COLLATE "pg_catalog"."default",
  "mac" varchar(255) COLLATE "pg_catalog"."default",
  CONSTRAINT "grid_first_level_info_new_pkey" PRIMARY KEY ("community")
)
WITH (fillfactor=80)
;

ALTER TABLE "public"."grid_first_level_info" 
  OWNER TO "postgres";

COMMENT ON COLUMN "public"."grid_first_level_info"."community" IS '社区';

COMMENT ON COLUMN "public"."grid_first_level_info"."grid_leader" IS '网格长信息';

COMMENT ON COLUMN "public"."grid_first_level_info"."build_num" IS '楼栋数';

COMMENT ON COLUMN "public"."grid_first_level_info"."population" IS '人数';

COMMENT ON COLUMN "public"."grid_first_level_info"."inconvenience_num" IS '行动不便人数';

COMMENT ON COLUMN "public"."grid_first_level_info"."disable_num" IS '残疾人人数';

COMMENT ON COLUMN "public"."grid_first_level_info"."other_pop_num" IS '港澳台外籍人数';

COMMENT ON COLUMN "public"."grid_first_level_info"."geom" IS '地理信息';

COMMENT ON COLUMN "public"."grid_first_level_info"."overview" IS '概况';

COMMENT ON COLUMN "public"."grid_first_level_info"."area" IS '社区面积（平方公里）';

COMMENT ON COLUMN "public"."grid_first_level_info"."resident_population" IS '常住人口';

COMMENT ON COLUMN "public"."grid_first_level_info"."registered_population" IS '户籍人口';

COMMENT ON COLUMN "public"."grid_first_level_info"."total_population" IS '总居住人口';

COMMENT ON COLUMN "public"."grid_first_level_info"."location" IS '中心坐标';

COMMENT ON COLUMN "public"."grid_first_level_info"."mac" IS 'grid_leader字段的mac值';

COMMENT ON TABLE "public"."grid_first_level_info" IS '一级社区网格信息';"""

def get_data_range():
    """从环境变量获取数据范围"""
    return os.getenv("DATA_RANGE", "June 2024 - December 2024")

def get_data_range_cn():
    """从环境变量获取中文数据范围"""
    return os.getenv("DATA_RANGE_CN", "2024年6月至12月")