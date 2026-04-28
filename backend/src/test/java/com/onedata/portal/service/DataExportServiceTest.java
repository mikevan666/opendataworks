package com.onedata.portal.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class DataExportServiceTest {

    private DorisConnectionService dorisConnectionService;
    private DataExportService service;

    @BeforeEach
    void setUp() {
        dorisConnectionService = mock(DorisConnectionService.class);
        service = new DataExportService(dorisConnectionService, new ObjectMapper());
    }

    @Test
    void exportToCsvAddsUtf8BomAndEscapesValuesThatWouldBreakColumns() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("名称", "张三");
        row.put("备注,字段", "含逗号,双引号\"和\r\n换行");
        row.put("公式", "=1+1");

        when(dorisConnectionService.previewTableData(1L, "db1", "t_user", 100))
                .thenReturn(Arrays.asList(row));

        byte[] bytes = service.exportToCsv(1L, "db1", "t_user", 100);

        assertTrue(bytes.length >= 3);
        assertEquals((byte) 0xEF, bytes[0]);
        assertEquals((byte) 0xBB, bytes[1]);
        assertEquals((byte) 0xBF, bytes[2]);

        String csv = new String(bytes, StandardCharsets.UTF_8);
        assertEquals("\uFEFF名称,\"备注,字段\",公式\r\n"
                + "张三,\"含逗号,双引号\"\"和\r\n换行\",\"=1+1\"\r\n", csv);
    }
}
