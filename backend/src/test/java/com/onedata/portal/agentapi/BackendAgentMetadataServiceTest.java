package com.onedata.portal.agentapi;

import com.onedata.portal.agentapi.dto.AgentDatasourceResolution;
import com.onedata.portal.agentapi.dto.AgentInspectResponse;
import com.onedata.portal.entity.DataField;
import com.onedata.portal.entity.DataLineage;
import com.onedata.portal.entity.DataTable;
import com.onedata.portal.entity.DorisCluster;
import com.onedata.portal.entity.DorisDbUser;
import com.onedata.portal.agentapi.service.BackendAgentMetadataService;
import com.onedata.portal.mapper.DataFieldMapper;
import com.onedata.portal.mapper.DataLineageMapper;
import com.onedata.portal.mapper.DataTableMapper;
import com.onedata.portal.mapper.DorisClusterMapper;
import com.onedata.portal.mapper.DorisDbUserMapper;
import com.onedata.portal.service.LineageService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;

import java.util.Arrays;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class BackendAgentMetadataServiceTest {

    @Mock
    private DataTableMapper dataTableMapper;

    @Mock
    private DataFieldMapper dataFieldMapper;

    @Mock
    private DataLineageMapper dataLineageMapper;

    @Mock
    private DorisClusterMapper dorisClusterMapper;

    @Mock
    private DorisDbUserMapper dorisDbUserMapper;

    @Mock
    private LineageService lineageService;

    @Mock
    private DataSourceProperties dataSourceProperties;

    @InjectMocks
    private BackendAgentMetadataService backendAgentMetadataService;

    @Test
    void resolveDatasourceReturnsPlatformMysqlForPlatformSchema() {
        when(dataSourceProperties.getUrl()).thenReturn("jdbc:mysql://mysql:3306/opendataworks?serverTimezone=Asia/Shanghai");
        when(dataSourceProperties.getUsername()).thenReturn("platform_user");
        when(dataSourceProperties.getPassword()).thenReturn("platform_pass");

        AgentDatasourceResolution result = backendAgentMetadataService.resolveDatasource("opendataworks", null);

        assertEquals("mysql", result.getEngine());
        assertEquals("mysql", result.getHost());
        assertEquals(Integer.valueOf(3306), result.getPort());
        assertEquals("platform_user", result.getUser());
        assertEquals("platform_pass", result.getPassword());
        assertEquals("platform_runtime", result.getResolvedBy());
    }

    @Test
    void resolveDatasourceUsesReadonlyUserForDorisDatabase() {
        DataTable table = new DataTable();
        table.setId(1L);
        table.setClusterId(12L);
        table.setDbName("doris_ods");
        table.setStatus("active");

        DorisCluster cluster = new DorisCluster();
        cluster.setId(12L);
        cluster.setClusterName("cluster-a");
        cluster.setSourceType("DORIS");
        cluster.setFeHost("doris-fe");
        cluster.setFePort(9030);
        cluster.setUsername("cluster_user");
        cluster.setPassword("cluster_pass");

        DorisDbUser readonlyUser = new DorisDbUser();
        readonlyUser.setClusterId(12L);
        readonlyUser.setDatabaseName("doris_ods");
        readonlyUser.setReadonlyUsername("readonly_user");
        readonlyUser.setReadonlyPassword("readonly_pass");

        when(dataSourceProperties.getUrl()).thenReturn("jdbc:mysql://mysql:3306/opendataworks");
        when(dataTableMapper.selectList(any())).thenReturn(Collections.singletonList(table));
        when(dorisClusterMapper.selectById(12L)).thenReturn(cluster);
        when(dorisDbUserMapper.selectList(any())).thenReturn(Collections.singletonList(readonlyUser));

        AgentDatasourceResolution result = backendAgentMetadataService.resolveDatasource("doris_ods", "doris");

        assertEquals("doris", result.getEngine());
        assertEquals("readonly_user", result.getUser());
        assertEquals("readonly_pass", result.getPassword());
        assertEquals("readonly_user", result.getResolvedBy());
    }

    @Test
    void resolveDatasourceRejectsMultiClusterMatch() {
        DataTable first = new DataTable();
        first.setClusterId(1L);
        first.setDbName("ods");
        first.setStatus("active");
        DataTable second = new DataTable();
        second.setClusterId(2L);
        second.setDbName("ods");
        second.setStatus("active");

        when(dataSourceProperties.getUrl()).thenReturn("jdbc:mysql://mysql:3306/opendataworks");
        when(dataTableMapper.selectList(any())).thenReturn(Arrays.asList(first, second));

        IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> backendAgentMetadataService.resolveDatasource("ods", null)
        );

        assertTrue(exception.getMessage().contains("多个 cluster_id"));
    }

    @Test
    void inspectPreservesMetadataSnapshotShape() {
        DataTable table = new DataTable();
        table.setId(8L);
        table.setClusterId(3L);
        table.setDbName("doris_ods");
        table.setTableName("ads_sales_di");
        table.setTableComment("销售日报");
        table.setStatus("active");

        DataField field = new DataField();
        field.setTableId(8L);
        field.setFieldName("stat_day");
        field.setFieldType("date");
        field.setFieldComment("统计日期");

        DataLineage lineage = new DataLineage();
        lineage.setId(15L);
        lineage.setLineageType("table");
        lineage.setUpstreamTableId(8L);
        lineage.setDownstreamTableId(9L);

        DataTable downstream = new DataTable();
        downstream.setId(9L);
        downstream.setDbName("doris_ads");
        downstream.setTableName("ads_sales_summary_di");

        when(dataTableMapper.selectList(any())).thenReturn(Collections.singletonList(table));
        when(dataFieldMapper.selectList(any())).thenReturn(Collections.singletonList(field));
        when(dataLineageMapper.selectList(any())).thenReturn(Collections.singletonList(lineage));
        when(dataTableMapper.selectBatchIds(any())).thenReturn(Arrays.asList(table, downstream));

        AgentInspectResponse response = backendAgentMetadataService.inspect("doris_ods", "ads_sales_di", null, 12);

        assertEquals("metadata_snapshot", response.getKind());
        assertEquals(1, response.getTableCount());
        assertEquals("doris_ods", response.getDatabase());
        assertEquals("ads_sales_di", response.getTable());
        assertEquals("stat_day", response.getTables().get(0).getFields().get(0).getFieldName());
        assertEquals("doris_ads", response.getLineage().get(0).getDownstreamDb());
    }
}
