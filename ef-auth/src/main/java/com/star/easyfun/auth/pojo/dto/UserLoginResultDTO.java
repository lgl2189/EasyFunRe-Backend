package com.star.easyfun.auth.pojo.dto;

import com.star.easyfun.common.pojo.dto.JWTPairDTO;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.io.Serial;
import java.io.Serializable;

/**
 * @author ：Star
 * @description ：    登陆的结果
 * @date ：2026 3月 14 15:07
 */

@Data
@Accessors(chain = true)
@NoArgsConstructor
@AllArgsConstructor
public class UserLoginResultDTO implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;

    public UserLoginResultDTO(JWTPairDTO jwtpairDTO, String deviceId, Boolean newDevice) {
        this.accessToken = jwtpairDTO.getAccessToken();
        this.refreshToken = jwtpairDTO.getRefreshToken();
        this.deviceId = deviceId;
        this.newDevice = newDevice;
    }

    /**
     * 访问令牌
     */
    private String accessToken;
    /**
     * 刷新令牌
     */
    private String refreshToken;
    /**
     * 设备Id
     */
    private String deviceId;
    /**
     * 是否是新的设备Id
     */
    private Boolean newDevice;

    /**
     * 用户Id
     */
    private String userId;

    /**
     * 是否是新用户
     */
    private Boolean isNewUser;
}