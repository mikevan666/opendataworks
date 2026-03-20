package com.onedata.portal.agentapi.service;

import com.onedata.portal.agentapi.dto.AgentDatasourceResolution;
import com.onedata.portal.agentapi.dto.AgentReadQueryRequest;
import com.onedata.portal.agentapi.dto.AgentReadQueryResponse;
import lombok.RequiredArgsConstructor;
import net.sf.jsqlparser.JSQLParserException;
import net.sf.jsqlparser.parser.CCJSqlParserUtil;
import net.sf.jsqlparser.statement.Statements;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;

@Service
@RequiredArgsConstructor
public class BackendAgentQueryService implements AgentQueryService {

    private static final int DEFAULT_LIMIT = 200;
    private static final int MAX_LIMIT = 1000;
    private static final int DEFAULT_TIMEOUT_SECONDS = 30;
    private static final int MAX_TIMEOUT_SECONDS = 120;
    private static final Set<String> READ_ONLY_PREFIXES = new LinkedHashSet<>(
            Arrays.asList("SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN")
    );

    private final AgentMetadataService agentMetadataService;
    private final AgentJdbcExecutor agentJdbcExecutor;

    @Override
    public AgentReadQueryResponse readQuery(AgentReadQueryRequest request) {
        String database = trimToNull(request.getDatabase());
        String sql = trimToNull(request.getSql());
        if (!StringUtils.hasText(database)) {
            throw new IllegalArgumentException("database 不能为空");
        }
        if (!StringUtils.hasText(sql)) {
            throw new IllegalArgumentException("sql 不能为空");
        }

        validateReadOnlySql(sql);
        int limit = normalizeLimit(request.getLimit());
        int timeoutSeconds = normalizeTimeout(request.getTimeoutSeconds());
        String preferredEngine = trimToLower(request.getPreferredEngine());

        AgentDatasourceResolution datasource = agentMetadataService.resolveDatasource(database, preferredEngine);
        AgentJdbcExecutor.QueryExecutionResult execution = agentJdbcExecutor.executeReadOnlyQuery(
                datasource,
                sql,
                limit,
                timeoutSeconds
        );

        AgentReadQueryResponse response = new AgentReadQueryResponse();
        response.setDatabase(database);
        response.setEngine(datasource.getEngine());
        response.setSql(sql);
        response.setLimit(limit);
        response.setRows(execution.getRows());
        response.setRowCount(execution.getRowCount());
        response.setHasMore(execution.isHasMore());
        response.setDurationMs(execution.getDurationMs());
        return response;
    }

    void validateReadOnlySql(String sql) {
        Statements statements;
        try {
            statements = CCJSqlParserUtil.parseStatements(sql);
        } catch (JSQLParserException e) {
            throw new IllegalArgumentException("SQL 解析失败，仅支持单条只读 SQL");
        }
        if (statements == null || statements.getStatements() == null || statements.getStatements().isEmpty()) {
            throw new IllegalArgumentException("SQL 不能为空");
        }
        if (statements.getStatements().size() != 1) {
            throw new IllegalArgumentException("仅支持单条只读 SQL");
        }

        String sqlType = detectSqlType(sql);
        if (!READ_ONLY_PREFIXES.contains(sqlType)) {
            throw new IllegalArgumentException("仅支持只读 SQL");
        }
    }

    private String detectSqlType(String sql) {
        String text = String.valueOf(sql == null ? "" : sql).trim();
        int whitespace = text.indexOf(' ');
        String head = whitespace < 0 ? text : text.substring(0, whitespace);
        return head.toUpperCase(Locale.ROOT);
    }

    private int normalizeLimit(Integer limit) {
        if (limit == null || limit <= 0) {
            return DEFAULT_LIMIT;
        }
        return Math.min(limit, MAX_LIMIT);
    }

    private int normalizeTimeout(Integer timeoutSeconds) {
        if (timeoutSeconds == null || timeoutSeconds <= 0) {
            return DEFAULT_TIMEOUT_SECONDS;
        }
        return Math.min(timeoutSeconds, MAX_TIMEOUT_SECONDS);
    }

    private String trimToNull(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim();
    }

    private String trimToLower(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim().toLowerCase(Locale.ROOT);
    }
}
