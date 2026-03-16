package com.star.easyfun.auth.config.property;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 3月 16 16:50
 */

@Data
@Component
@ConfigurationProperties(prefix = "easyfun.device")
public class DeviceExpirationProperty {
    private Integer expiration;
}