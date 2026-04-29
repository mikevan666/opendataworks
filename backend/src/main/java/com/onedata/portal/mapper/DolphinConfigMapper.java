package com.onedata.portal.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.onedata.portal.entity.DolphinConfig;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface DolphinConfigMapper extends BaseMapper<DolphinConfig> {

    @Select("SELECT COUNT(1) FROM data_workflow "
            + "WHERE dolphin_config_id = #{configId} "
            + "AND workflow_code IS NOT NULL "
            + "AND workflow_code > 0 "
            + "AND (deleted IS NULL OR deleted = 0)")
    Long countRuntimeBoundWorkflows(@Param("configId") Long configId);
}
