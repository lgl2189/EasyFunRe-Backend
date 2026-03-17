package com.star.easyfun.auth.service;

/**
 * @author ：Star
 * @description ：    与DeviceId相关服务接口实现
 * @date ：2026 2月 24 20:10
 */
// TODO: 当前过期设备码的清理依托于用户访问，如果用户再也没有登录过，过期的设备码就不会被删除，可以增加定时删除机制，不重要，暂不实现
public interface DeviceService {

    /**
     * 检查设备码是否已经被该用户使用，同时刷新提供的设备码的过期时间
     *
     * @param userId 用户ID
     * @param deviceId 需要检查的设备码
     * @return true：设备码存在，false：设备码不存在
     */
    boolean isDeviceIdExist(String userId, String deviceId);

    /**
     * 缓存设备码，如果已存在则刷新过期时间
     * @param userId 用户ID
     * @param deviceId 设备码
     */
    void cacheDeviceId(String userId, String deviceId);

    /**
     * 生成新的设备码，保证生成的设备码不与已有的冲突
     * @param userId 用户ID
     * @return 新的设备码
     */
    String generateDeviceId(String userId);

    /**
     * 删除设备码
     * @param userId 用户ID
     * @param deviceId 设备码
     */
    void removeDeviceId(String userId, String deviceId);
}
