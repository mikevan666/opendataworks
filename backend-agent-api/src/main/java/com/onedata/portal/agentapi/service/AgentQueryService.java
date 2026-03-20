package com.onedata.portal.agentapi.service;

import com.onedata.portal.agentapi.dto.AgentReadQueryRequest;
import com.onedata.portal.agentapi.dto.AgentReadQueryResponse;

public interface AgentQueryService {

    AgentReadQueryResponse readQuery(AgentReadQueryRequest request);
}
