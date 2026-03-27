package com.star.easyfun.content.config.property;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 3月 26 18:34
 */

@Data
@Component
@ConfigurationProperties(prefix = "minio")
public class MinioProperty {
    private String endpoint;
    private String accessKey;
    private String secretKey;
    private String bucket;
    private Integer expirySeconds;
}