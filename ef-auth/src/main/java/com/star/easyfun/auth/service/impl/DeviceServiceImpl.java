package com.star.easyfun.auth.service.impl;

import com.star.easyfun.auth.config.property.DeviceExpirationProperty;
import com.star.easyfun.auth.service.DeviceService;
import com.star.easyfun.auth.util.DeviceIdUtil;
import com.star.easyfun.common.constant.CommonRedisKey;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

/**
 * @author ：Star
 * @description ：无描述
 * @date ：2026 3月 14 14:03
 */

@Service
@RequiredArgsConstructor
public class DeviceServiceImpl implements DeviceService {

    private final RedisTemplate<String, Object> redisTemplate;
    private final DeviceExpirationProperty deviceExpirationProperty;

    @Override
    public boolean isDeviceIdExist(String userId, String deviceId) {
        String key = CommonRedisKey.getDeviceIdKey(userId);
        if (!redisTemplate.hasKey(key)) {
            return false;
        }
        // 先删除已过期的设备码
        long now = System.currentTimeMillis();
        redisTemplate.opsForZSet().removeRangeByScore(key, 0, now);
        // 等于null说明没有查询到该设备码，也就是该设备码不存在，返回false
        return !(redisTemplate.opsForZSet().score(key, deviceId) == null);
    }

    @Override
    public void cacheDeviceId(String userId, String deviceId) {
        String key = CommonRedisKey.getDeviceIdKey(userId);
        long expiration = System.currentTimeMillis() + TimeUnit.DAYS.toMillis(deviceExpirationProperty.getExpiration());
        redisTemplate.opsForZSet().add(key, deviceId, expiration);
    }

    @Override
    public String generateDeviceId(String userId) {
        String newDeviceId = DeviceIdUtil.generate();
        while (isDeviceIdExist(userId, newDeviceId)) {
            newDeviceId = DeviceIdUtil.generate();
        }
        cacheDeviceId(userId, newDeviceId);
        return newDeviceId;
    }

    @Override
    public void removeDeviceId(String userId, String deviceId) {
        String key = CommonRedisKey.getDeviceIdKey(userId);
        redisTemplate.opsForZSet().remove(key, deviceId);
    }
}