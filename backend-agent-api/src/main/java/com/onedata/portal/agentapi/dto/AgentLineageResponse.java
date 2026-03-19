package com.onedata.portal.agentapi.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class AgentLineageResponse {
    private String kind = "lineage_snapshot";

    @JsonProperty("db_name")
    private String dbName;

    private String table;

    @JsonProperty("table_id")
    private Long tableId;
    private Integer depth;
    private List<AgentLineageRecord> lineage = new ArrayList<>();
    private String error;
}
