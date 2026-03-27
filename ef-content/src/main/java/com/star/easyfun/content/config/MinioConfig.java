package com.star.easyfun.content.config;

import com.star.easyfun.content.config.property.MinioProperty;
import io.minio.MinioClient;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * @author ：Star
 * @description ：    MinIO配置类
 * @date ：2026 3月 26 18:07
 */

@Configuration
@RequiredArgsConstructor
public class MinioConfig {
    private final MinioProperty minioProperty;

    @Bean
    public MinioClient minioClient() {
        return MinioClient.builder()
                .endpoint(minioProperty.getEndpoint())
                .credentials(minioProperty.getAccessKey(), minioProperty.getSecretKey())
                .build();
    }
}