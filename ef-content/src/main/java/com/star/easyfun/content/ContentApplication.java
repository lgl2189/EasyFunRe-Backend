package com.star.easyfun.content;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * @author ：Star
 * @description ：    User微服务启动类
 * @date ：2026 2月 21 22:32
 */

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@EnableAsync
public class ContentApplication {
    public static void main(String[] args) {
        System.setProperty("nacos.logging.default.config.enabled","false");
        SpringApplication.run(ContentApplication.class, args);
    }

}