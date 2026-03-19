package com.onedata.portal.agentapi.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class AgentInspectResponse {
    private String kind = "metadata_snapshot";
    private String database;
    private String table;
    private String keyword;

    @JsonProperty("table_count")
    private int tableCount;

    private List<AgentTableMetadata> tables = new ArrayList<>();
    private List<AgentLineageRecord> lineage = new ArrayList<>();
    private String error;
}
