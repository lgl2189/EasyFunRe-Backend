package com.star.easyfun.auth.service;

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
