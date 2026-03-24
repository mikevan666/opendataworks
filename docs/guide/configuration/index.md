# 配置说明

## 后端配置 (application.yml)

```yaml
server:
  port: 8080
  servlet:
    context-path: /api

spring:
  application:
    name: opendataworks

  # 数据库配置
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/opendataworks?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true
    username: opendataworks
    password: opendataworks123

  # Jackson 配置
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: GMT+8
    serialization:
      write-dates-as-timestamps: false

# MyBatis Plus 配置
mybatis-plus:
  mapper-locations: classpath*:/mapper/**/*.xml
  type-aliases-package: com.onedata.portal.entity
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl

# DolphinScheduler 配置默认由数据库 dolphin_config 表管理，
# 推荐通过前端“系统管理 -> Dolphin 配置”维护，而不是直接写入 application.yml

# 日志配置
logging:
  level:
    com.onedata.portal: debug
    org.springframework.web: info
```

## 前端配置 (vite.config.js)

```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api/v1/dataagent': {
        target: 'http://localhost:8900',
        changeOrigin: true
      },
      '/api/v1/nl2sql': {
        target: 'http://localhost:8900',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
```
