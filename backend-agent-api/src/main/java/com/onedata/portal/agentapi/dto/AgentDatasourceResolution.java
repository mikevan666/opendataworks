package com.onedata.portal.agentapi.dto;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class AgentDatasourceResolution {
    private String engine;
    private String database;

    @JsonIgnore
    private String host;

    @JsonIgnore
    private Integer port;

    @JsonIgnore
    private String user;

    @JsonIgnore
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
