package com.onedata.portal.agentapi.controller;

import com.onedata.portal.agentapi.dto.AgentReadQueryRequest;
import com.onedata.portal.agentapi.dto.AgentReadQueryResponse;
import com.onedata.portal.agentapi.service.AgentQueryService;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/ai/query")
public class AgentQueryController {

    private final AgentQueryService agentQueryService;

    @PostMapping("/read")
    public AgentReadQueryResponse read(@Validated @RequestBody AgentReadQueryRequest request) {
        return agentQueryService.readQuery(request);
    }
}
