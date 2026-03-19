package com.onedata.portal.agentapi.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "agent.api")
public class AgentApiProperties {

    /**
     * 服务间访问 token，必须通过请求头携带。
     */
    private String serviceToken = "";

    /**
     * 读取服务 token 的请求头名称。
     */
    private String tokenHeaderName = "X-Agent-Service-Token";

    /**
     * 是否仅允许私网/本机访问。
     */
    private boolean requirePrivateNetwork = true;
}
