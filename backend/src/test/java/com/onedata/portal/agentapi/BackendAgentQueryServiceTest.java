package com.onedata.portal.agentapi;

import com.onedata.portal.agentapi.dto.AgentDatasourceResolution;
import com.onedata.portal.agentapi.dto.AgentReadQueryRequest;
import com.onedata.portal.agentapi.dto.AgentReadQueryResponse;
import com.onedata.portal.agentapi.service.AgentJdbcExecutor;
import com.onedata.portal.agentapi.service.AgentMetadataService;
import com.onedata.portal.agentapi.service.BackendAgentQueryService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class BackendAgentQueryServiceTest {

    @Mock
    private AgentMetadataService agentMetadataService;

    @Mock
    private AgentJdbcExecutor agentJdbcExecutor;

    @InjectMocks
    private BackendAgentQueryService backendAgentQueryService;

    @Test
    void readQueryDelegatesToDatasourceResolverAndJdbcExecutor() {
        AgentReadQueryRequest request = new AgentReadQueryRequest();
        request.setDatabase("opendataworks");
        request.setSql("SELECT 1");
        request.setPreferredEngine("mysql");
        request.setLimit(50);
        request.setTimeoutSeconds(20);

        AgentDatasourceResolution datasource = new AgentDatasourceResolution();
        datasource.setDatabase("opendataworks");
        datasource.setEngine("mysql");
        when(agentMetadataService.resolveDatasource("opendataworks", "mysql")).thenReturn(datasource);

        AgentJdbcExecutor.QueryExecutionResult execution = new AgentJdbcExecutor.QueryExecutionResult();
        execution.setRows(Collections.singletonList(Collections.singletonMap("value", 1)));
        execution.setRowCount(1);
        execution.setHasMore(false);
        execution.setDurationMs(12);
        when(agentJdbcExecutor.executeReadOnlyQuery(datasource, "SELECT 1", 50, 20)).thenReturn(execution);

        AgentReadQueryResponse response = backendAgentQueryService.readQuery(request);

        assertEquals("query_result", response.getKind());
        assertEquals("opendataworks", response.getDatabase());
        assertEquals("mysql", response.getEngine());
        assertEquals(Integer.valueOf(1), response.getRowCount());
        assertEquals(Integer.valueOf(12), response.getDurationMs());
        verify(agentMetadataService).resolveDatasource("opendataworks", "mysql");
        verify(agentJdbcExecutor).executeReadOnlyQuery(datasource, "SELECT 1", 50, 20);
    }

    @Test
    void readQueryRejectsMutatingSql() {
        AgentReadQueryRequest request = new AgentReadQueryRequest();
        request.setDatabase("opendataworks");
        request.setSql("INSERT INTO demo VALUES (1)");

        IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> backendAgentQueryService.readQuery(request)
        );

        assertEquals("仅支持只读 SQL", exception.getMessage());
    }

    @Test
    void readQueryRejectsMultipleStatements() {
        AgentReadQueryRequest request = new AgentReadQueryRequest();
        request.setDatabase("opendataworks");
        request.setSql("SELECT 1; SELECT 2");

        IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> backendAgentQueryService.readQuery(request)
        );

        assertEquals("仅支持单条只读 SQL", exception.getMessage());
    }

    @Test
    void readQueryClampsLimitAndTimeout() {
        AgentReadQueryRequest request = new AgentReadQueryRequest();
        request.setDatabase("opendataworks");
        request.setSql("SELECT 1");
        request.setLimit(5000);
        request.setTimeoutSeconds(500);

        AgentDatasourceResolution datasource = new AgentDatasourceResolution();
        datasource.setDatabase("opendataworks");
        datasource.setEngine("mysql");
        when(agentMetadataService.resolveDatasource("opendataworks", null)).thenReturn(datasource);
        when(agentJdbcExecutor.executeReadOnlyQuery(any(), eq("SELECT 1"), eq(1000), eq(120)))
                .thenReturn(new AgentJdbcExecutor.QueryExecutionResult());

        backendAgentQueryService.readQuery(request);

        verify(agentJdbcExecutor).executeReadOnlyQuery(datasource, "SELECT 1", 1000, 120);
    }
}
