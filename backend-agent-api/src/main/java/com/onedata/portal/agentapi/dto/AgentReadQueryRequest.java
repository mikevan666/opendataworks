package com.onedata.portal.agentapi.dto;

import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
public class AgentReadQueryRequest {

    @NotBlank(message = "database 不能为空")
    private String database;

    @NotBlank(message = "sql 不能为空")
    private String sql;

    private String preferredEngine;

    private Integer limit;

    private Integer timeoutSeconds;
}
