package com.onedata.portal.agentapi.service;

import com.onedata.portal.agentapi.dto.AgentDatasourceResolution;
import com.onedata.portal.config.DorisJdbcProperties;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentJdbcExecutor {

    private final DorisJdbcProperties dorisJdbcProperties;

    public QueryExecutionResult executeReadOnlyQuery(
            AgentDatasourceResolution datasource,
            String sql,
            int limit,
            int timeoutSeconds
    ) {
        long start = System.currentTimeMillis();
        try (Connection connection = openConnection(datasource, datasource.getDatabase());
             Statement statement = connection.createStatement()) {
            statement.setQueryTimeout(timeoutSeconds);
            boolean hasResultSet = statement.execute(sql);
            if (!hasResultSet) {
                throw new IllegalArgumentException("只读 SQL 必须返回结果集");
            }

            List<Map<String, Object>> rows = new ArrayList<>();
            boolean hasMore = false;
            try (ResultSet resultSet = statement.getResultSet()) {
                ResultSetMetaData metaData = resultSet.getMetaData();
                int columnCount = metaData.getColumnCount();
                while (resultSet.next()) {
                    if (rows.size() >= limit) {
                        hasMore = true;
                        break;
                    }
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (int i = 1; i <= columnCount; i++) {
                        row.put(metaData.getColumnLabel(i), resultSet.getObject(i));
                    }
                    rows.add(row);
                }
            }

            QueryExecutionResult result = new QueryExecutionResult();
            result.setRows(rows);
            result.setRowCount(rows.size());
            result.setHasMore(hasMore);
            result.setDurationMs((int) (System.currentTimeMillis() - start));
            return result;
        } catch (SQLException e) {
            throw new RuntimeException("执行只读 SQL 失败: " + e.getMessage(), e);
        }
    }

    public String fetchTableDdl(
            AgentDatasourceResolution datasource,
            String database,
            String tableName,
            int timeoutSeconds
    ) {
        String sql = "SHOW CREATE TABLE `" + escapeIdentifier(database) + "`.`" + escapeIdentifier(tableName) + "`";
        try (Connection connection = openConnection(datasource, database);
             Statement statement = connection.createStatement()) {
            statement.setQueryTimeout(timeoutSeconds);
            try (ResultSet resultSet = statement.executeQuery(sql)) {
                if (resultSet.next()) {
                    ResultSetMetaData metaData = resultSet.getMetaData();
                    int ddlColumn = metaData.getColumnCount() >= 2 ? 2 : 1;
                    return resultSet.getString(ddlColumn);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException("获取建表语句失败: " + e.getMessage(), e);
        }
        throw new RuntimeException(String.format("表 %s.%s 不存在", database, tableName));
    }

    private Connection openConnection(AgentDatasourceResolution datasource, String database) throws SQLException {
        String targetDatabase = StringUtils.hasText(database) ? database.trim() : datasource.getDatabase();
        String url = buildJdbcUrl(datasource, targetDatabase);
        Connection connection = DriverManager.getConnection(
                url,
                trimToEmpty(datasource.getUser()),
                trimToEmpty(datasource.getPassword())
        );
        applySessionCharset(connection);
        return connection;
    }

    private String buildJdbcUrl(AgentDatasourceResolution datasource, String database) {
        String template = dorisJdbcProperties.getUrlTemplate();
        if (!StringUtils.hasText(template)) {
            throw new IllegalStateException("doris.jdbc.url-template 未配置");
        }
        String host = StringUtils.hasText(datasource.getHost()) ? datasource.getHost().trim() : "localhost";
        int port = datasource.getPort() == null ? 3306 : datasource.getPort();
        String targetDatabase = StringUtils.hasText(database) ? database.trim() : datasource.getDatabase();
        if (!StringUtils.hasText(targetDatabase)) {
            throw new IllegalArgumentException("database 不能为空");
        }
        return String.format(template, host, port, targetDatabase);
    }

    private void applySessionCharset(Connection connection) {
        if (!dorisJdbcProperties.isSessionCharsetEnabled()) {
            return;
        }
        String primaryCharset = dorisJdbcProperties.getSessionCharset();
        if (!StringUtils.hasText(primaryCharset)) {
            return;
        }
        try (Statement statement = connection.createStatement()) {
            statement.execute("SET NAMES " + primaryCharset);
        } catch (SQLException primaryEx) {
            String fallbackCharset = dorisJdbcProperties.getSessionCharsetFallback();
            if (!StringUtils.hasText(fallbackCharset) || fallbackCharset.equalsIgnoreCase(primaryCharset)) {
                log.warn("Failed to set agent JDBC charset to {}. reason={}", primaryCharset, primaryEx.getMessage());
                return;
            }
            try (Statement statement = connection.createStatement()) {
                statement.execute("SET NAMES " + fallbackCharset);
            } catch (SQLException fallbackEx) {
                log.warn("Failed to set agent JDBC fallback charset to {}. reason={}", fallbackCharset, fallbackEx.getMessage());
            }
        }
    }

    private String escapeIdentifier(String value) {
        return String.valueOf(value == null ? "" : value).replace("`", "``");
    }

    private String trimToEmpty(String value) {
        return value == null ? "" : value.trim();
    }

    @Data
    public static class QueryExecutionResult {
        private List<Map<String, Object>> rows = new ArrayList<>();
        private int rowCount;
        private boolean hasMore;
        private int durationMs;
    }
}
