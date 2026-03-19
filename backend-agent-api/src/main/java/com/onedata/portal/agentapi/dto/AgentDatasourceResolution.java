package com.onedata.portal.agentapi.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class AgentDatasourceResolution {
    private String engine;
    private String database;
    private String host;
    private Integer port;
    private String user;
    private String password;

    @JsonProperty("source_type")
    private String sourceType;

    @JsonProperty("cluster_id")
    private Long clusterId;

    @JsonProperty("cluster_name")
    private String clusterName;

    @JsonProperty("resolved_by")
    private String resolvedBy;
}
